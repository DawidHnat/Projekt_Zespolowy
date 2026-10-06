#!/usr/bin/env python3
"""Configure Fleet-Flow VM start/deallocation schedules without changing cloud-init."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
SCHEDULES = [
    ("weekday-start", "start", WEEKDAYS, 15, "ScheduledTime"),
    ("nightly-shutdown", "deallocate", WEEKDAYS, 22, "EveryNight"),
    ("saturday-start", "start", ["Saturday"], 8, "ScheduledTime"),
    ("sunday-start", "start", ["Sunday"], 12, "ScheduledTime"),
    ("weekend-shutdown", "deallocate", ["Saturday", "Sunday"], 21, "ScheduledTime"),
]


def build_template(vm_name, location):
    resources = []
    for operation in ("start", "deallocate"):
        role_id = f"[guid(resourceGroup().id, '{vm_name}', '{operation}-role')]"
        resources.append({
            "type": "Microsoft.Authorization/roleDefinitions",
            "apiVersion": "2022-04-01",
            "name": role_id,
            "properties": {
                "roleName": f"[concat('Fleet-Flow {operation} ', guid(resourceGroup().id, '{vm_name}', '{operation}-role'))]",
                "description": f"Only {operation} the Fleet-Flow development VM.",
                "type": "CustomRole",
                "assignableScopes": ["[resourceGroup().id]"],
                "permissions": [{"actions": [f"Microsoft.Compute/virtualMachines/{operation}/action"], "notActions": [], "dataActions": [], "notDataActions": []}],
            },
        })
    vm_id = f"resourceId('Microsoft.Compute/virtualMachines', '{vm_name}')"
    for suffix, operation, days, hour, trigger_name in SCHEDULES:
        name = f"{vm_name}-{suffix}"
        workflow_id = f"resourceId('Microsoft.Logic/workflows', '{name}')"
        role_id = f"guid(resourceGroup().id, '{vm_name}', '{operation}-role')"
        # Keep the previously deployed shutdown role assignment and identity.
        assignment = "shutdown-assignment" if suffix == "nightly-shutdown" else f"{suffix}-assignment"
        resources.extend([{
            "type": "Microsoft.Logic/workflows",
            "apiVersion": "2019-05-01",
            "name": name,
            "location": location,
            "tags": {"project": "fleet-flow", "environment": "development", "managedBy": "ARM"},
            "identity": {"type": "SystemAssigned"},
            "properties": {
                # Enable only after all VM-scoped permissions have been assigned.
                "state": "Disabled",
                "definition": {
                    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                    "contentVersion": "1.0.0.0",
                    "parameters": {},
                    "triggers": {trigger_name: {
                        "type": "Recurrence",
                        "recurrence": {
                            "frequency": "Week", "interval": 1,
                            "timeZone": "Central European Standard Time",
                            # A past Monday anchors weekly schedules without an
                            # immediate first run or a future-start grace period.
                            "startTime": "2020-01-06T00:00:00",
                            "schedule": {"weekDays": days, "hours": [hour], "minutes": [0]},
                        },
                    }},
                    "actions": {"ControlDevelopmentVM": {
                        "type": "Http",
                        "operationOptions": "DisableAsyncPattern",
                        "inputs": {
                            "method": "POST",
                            "uri": f"[concat('https://management.azure.com', {vm_id}, '/{operation}?api-version=2024-03-01')]",
                            "authentication": {"type": "ManagedServiceIdentity", "audience": "https://management.azure.com/"},
                        },
                        "runAfter": {},
                    }},
                    "outputs": {},
                },
            },
        }, {
            "type": "Microsoft.Compute/virtualMachines/providers/roleAssignments",
            "apiVersion": "2022-04-01",
            "name": f"[concat('{vm_name}/Microsoft.Authorization/', guid(resourceGroup().id, '{vm_name}', '{assignment}'))]",
            "dependsOn": [f"[{workflow_id}]", f"[resourceId('Microsoft.Authorization/roleDefinitions', {role_id})]"],
            "properties": {
                "roleDefinitionId": f"[resourceId('Microsoft.Authorization/roleDefinitions', {role_id})]",
                "principalId": f"[reference({workflow_id}, '2019-05-01', 'Full').identity.principalId]",
                "principalType": "ServicePrincipal",
            },
        }])
    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0", "resources": resources,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subscription", required=True)
    parser.add_argument("--resource-group", default="fleet-flow-dev-rg")
    parser.add_argument("--vm-name", default="fleet-flow-dev")
    parser.add_argument("--location", default="polandcentral")
    parser.add_argument("--state", choices=("enabled", "disabled"), default="enabled")
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,39}", args.vm_name):
        parser.error("Nazwa VM musi zawierać 3–40 małych liter, cyfr lub myślników.")
    directory = ROOT / ".local"
    directory.mkdir(exist_ok=True, mode=0o700)
    template = directory / "power-template.json"
    template.write_text(json.dumps(build_template(args.vm_name, args.location), indent=2) + "\n")
    os.chmod(template, 0o600)
    print(f"Harmonogramy: {template}", flush=True)
    print("Europe/Warsaw: pon.–pt. 15–22, sob. 8–21, nd. 12–21.", flush=True)
    if args.render_only:
        return

    def az(arguments):
        return ["az"] + arguments + ["--subscription", args.subscription, "--only-show-errors"]

    subscription = json.loads(subprocess.check_output(az(["rest", "--method", "get", "--url", f"https://management.azure.com/subscriptions/{args.subscription}?api-version=2022-12-01", "-o", "json"]), text=True))
    policies = subscription.get("subscriptionPolicies", {})
    if subscription.get("state") != "Enabled" or not policies.get("quotaId", "").startswith("AzureForStudents") or policies.get("spendingLimit") != "On":
        raise ValueError("Wymagana aktywna subskrypcja Azure for Students z limitem wydatków.")
    vm = json.loads(subprocess.check_output(az(["vm", "show", "-g", args.resource_group, "-n", args.vm_name, "--query", "{id:id,location:location}", "-o", "json"]), text=True))
    if vm["location"].lower() != args.location.lower():
        raise ValueError("Region harmonogramu musi być taki sam jak region istniejącej VM.")
    subprocess.run(az(["deployment", "group", "validate" if args.validate_only else "create", "-g", args.resource_group, "--name", "fleet-flow-power-schedule", "--mode", "Incremental", "--template-file", str(template), "--query", "{error:error,state:properties.provisioningState}", "-o", "json"]), check=True)
    if args.validate_only:
        return
    if args.state == "enabled":
        for suffix, *_ in SCHEDULES:
            url = f"https://management.azure.com/subscriptions/{args.subscription}/resourceGroups/{args.resource_group}/providers/Microsoft.Logic/workflows/{args.vm_name}-{suffix}/enable?api-version=2016-06-01"
            subprocess.run(az(["rest", "--method", "post", "--url", url, "--body", "{}", "-o", "none"]), check=True)
    print(f"Harmonogramy {args.state}; bieżący stan VM nie jest zmieniany.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
