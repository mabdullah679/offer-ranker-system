"""Master orchestrator script for local workflows."""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import List

LOG_ROOT = Path("/tmp/offer_ranker_logs")
PROJECT_ROOT = Path(__file__).parent


class Orchestrator:
    def __init__(self) -> None:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        self.log_dir = LOG_ROOT / timestamp
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, step: str) -> Path:
        safe_step = step.replace(":", "_").replace("/", "_")
        return self.log_dir / f"{safe_step}.log"

    def run_step(self, step: str, command: List[str], cwd: Path | None = None) -> Path:
        log_path = self._log_path(step)
        print(f"[orchestrate] Starting {step}... logs -> {log_path}")
        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write(f"Running command: {' '.join(command)}\n")
            log_file.flush()
            process = subprocess.Popen(
                command,
                cwd=str(cwd) if cwd else None,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
            try:
                returncode = process.wait()
            except KeyboardInterrupt:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                print(f"[orchestrate] {step} interrupted. Logs at {log_path}")
                return Path(log_path)

        if returncode != 0:
            print(f"[orchestrate] {step} failed with exit code {returncode}. See logs at {log_path}")
            raise SystemExit(returncode)

        print(f"[orchestrate] Step {step} completed successfully. Full logs at: {log_path}")
        return log_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Orchestrate Offer Ranker workflows")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("train", help="Run the training pipeline")
    subparsers.add_parser("api:local", help="Run the API locally via uvicorn")
    subparsers.add_parser("test", help="Run pytest suite")
    subparsers.add_parser("docker:build", help="Build the Docker image")
    subparsers.add_parser("docker:run", help="Run the Docker image locally")
    subparsers.add_parser("tf:init", help="Run terraform init")
    subparsers.add_parser("tf:plan", help="Run terraform plan")
    subparsers.add_parser("tf:apply", help="Run terraform apply with confirmation")
    subparsers.add_parser("deploy", help="Guided deployment workflow")

    smoke = subparsers.add_parser("smoke-test", help="Run the smoke test script")
    smoke.add_argument("--url", required=True, help="Base URL for the deployed service")

    return parser


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    orch = Orchestrator()

    python_exec = sys.executable

    if args.command == "train":
        orch.run_step("train", [python_exec, "-m", "scripts.train_model"])

    elif args.command == "api:local":
        print("[orchestrate] API will run on http://127.0.0.1:8080 by default. Use CTRL+C to stop.")
        print("[orchestrate] Try: curl http://127.0.0.1:8080/health")
        port_value = os.getenv("PORT", "8080")
        try:
            port_int = int(port_value)
        except ValueError:
            print(f"[orchestrate] Invalid PORT value '{port_value}'. Please provide an integer.")
            raise SystemExit(1)
        if port_in_use(port_int):
            print(f"[orchestrate] Port {port_int} appears to be in use. Stop the other process or set PORT to a different value.")
            raise SystemExit(1)
        orch.run_step("api_local", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port_value])

    elif args.command == "test":
        orch.run_step("pytest", ["pytest"])

    elif args.command == "docker:build":
        image_tag = os.getenv("IMAGE_NAME", "offer-ranker-api:local")
        orch.run_step("docker_build", ["docker", "build", "-t", image_tag, "."])

    elif args.command == "docker:run":
        port = os.getenv("PORT", "8080")
        image_tag = os.getenv("IMAGE_NAME", "offer-ranker-api:local")
        print(f"[orchestrate] Mapping local port {port}. Hit http://127.0.0.1:{port}/health once running.")
        orch.run_step(
            "docker_run",
            [
                "docker",
                "run",
                "--rm",
                "-p",
                f"{port}:{port}",
                "-e",
                f"PORT={port}",
                image_tag,
            ],
        )

    elif args.command == "tf:init":
        orch.run_step("terraform_init", ["terraform", "init", "-input=false"], cwd=PROJECT_ROOT / "infrastructure")

    elif args.command == "tf:plan":
        orch.run_step(
            "terraform_plan",
            ["terraform", "plan", "-input=false"],
            cwd=PROJECT_ROOT / "infrastructure",
        )

    elif args.command == "tf:apply":
        confirmation = input("Proceed with terraform apply? (y/N): ").strip().lower()
        if confirmation not in {"y", "yes"}:
            print("[orchestrate] Aborting terraform apply.")
            raise SystemExit(0)
        orch.run_step(
            "terraform_apply",
            ["terraform", "apply", "-input=false", "-auto-approve"],
            cwd=PROJECT_ROOT / "infrastructure",
        )

    elif args.command == "deploy":
        print("[orchestrate] Starting guided deploy: tests -> docker build -> terraform plan.")
        orch.run_step("deploy_tests", ["pytest"])
        image_tag = os.getenv("DEPLOY_IMAGE_TAG", "offer-ranker-api:deploy")
        orch.run_step("deploy_docker_build", ["docker", "build", "-t", image_tag, "."])
        plan_log = orch.run_step(
            "deploy_tf_plan",
            ["terraform", "plan", "-input=false"],
            cwd=PROJECT_ROOT / "infrastructure",
        )
        print("[orchestrate] Deployment prep finished. Push image/tag via your preferred flow and review plan logs at", plan_log)
        print("[orchestrate] Terraform apply still requires manual confirmation (see orchestrate tf:apply or deploy workflow).")

    elif args.command == "smoke-test":
        url = args.url
        orch.run_step("smoke_test", ["bash", "scripts/smoke_test.sh", url])

    else:  # pragma: no cover
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
