"""CodeDeploy and EC2 orchestration."""

import os
import time
from dataclasses import dataclass

from .artifacts import CodeDeployArtifacts
from .cli import AwsCli
from .terraform import TerraformOutputs


@dataclass
class AwsDemoOrchestrator:
    aws: AwsCli
    outputs: TerraformOutputs
    artifacts: CodeDeployArtifacts

    def instance_id(self, target: str) -> str:
        return self.outputs[f"{target}_instance_id"]

    def start_instance(self, target: str) -> None:
        instance_id = self.instance_id(target)
        self.aws.run("ec2", "start-instances", "--instance-ids", instance_id)
        self.aws.run("ec2", "wait", "instance-running", "--instance-ids", instance_id)
        self.aws.run("ec2", "wait", "instance-status-ok", "--instance-ids", instance_id)

    def stop_instance(self, target: str) -> None:
        instance_id = self.instance_id(target)
        self.aws.run("ec2", "stop-instances", "--instance-ids", instance_id)
        self.aws.run("ec2", "wait", "instance-stopped", "--instance-ids", instance_id)

    def deploy(self, target: str) -> None:
        bundle_name = "okapi-stack" if target == "okapi" else "otel-demo"
        application = self.outputs[f"{target}_codedeploy_app"]
        group = self.outputs[f"{target}_codedeploy_group"]
        key = self.artifacts.upload(bundle_name, self.outputs["codedeploy_artifact_bucket"])
        deployment_id = self.aws.run(
            "deploy", "create-deployment",
            "--application-name", application,
            "--deployment-group-name", group,
            "--s3-location", f"bucket={self.outputs['codedeploy_artifact_bucket']},key={key},bundleType=zip",
            "--query", "deploymentId", "--output", "text", capture=True,
        )
        self.wait(deployment_id)

    def wait(self, deployment_id: str) -> None:
        while True:
            status = self.aws.run(
                "deploy", "get-deployment", "--deployment-id", deployment_id,
                "--query", "deploymentInfo.status", "--output", "text", capture=True,
            )
            print(f"deployment {deployment_id}: {status}")
            if status == "Succeeded":
                return
            if status in {"Failed", "Stopped"}:
                raise RuntimeError(f"deployment {deployment_id} ended with {status}")
            time.sleep(10)

    def converge(self) -> None:
        self.start_instance("okapi")
        self.deploy("okapi")
        self.start_instance("otel")
        self.deploy("otel")

    def stop(self) -> None:
        self.stop_instance("otel")
        self.stop_instance("okapi")

    def status(self) -> None:
        self.aws.run(
            "ec2", "describe-instances",
            "--instance-ids", self.instance_id("okapi"), self.instance_id("otel"),
            "--query",
            "Reservations[].Instances[].{Id:InstanceId,State:State.Name,PublicIp:PublicIpAddress,PrivateIp:PrivateIpAddress,Name:Tags[?Key=='Name']|[0].Value}",
            "--output", "table",
        )
        print(f"Okapi: {self.outputs['okapi_url']}")
        print(f"Otel:  {self.outputs['otel_url']}")

    def set_openai_key(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY is required")
        self.aws.put_parameter(
            f"{self.outputs['ssm_prefix']}/secrets/openai_api_key",
            key,
            secure=True,
        )
