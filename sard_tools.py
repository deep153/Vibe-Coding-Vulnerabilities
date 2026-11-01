"""OpenAI-compatible tool schema for sandboxed coding agents."""

EXECUTE_SANDBOXED_COMMAND_TOOL = {
    "type": "function",
    "function": {
        "name": "execute_sandboxed_command",
        "description": (
            "Executes a shell command in the workspace terminal. "
            "Default sandbox: workspace scope, no outbound network, no git credentials. "
            "Request elevated permissions only when strictly necessary."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute.",
                },
                "required_permissions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "sandbox_default",
                            "full_network",
                            "host_filesystem_write",
                            "git_credentials",
                        ],
                    },
                    "description": "Permissions required for this command.",
                },
                "user_summary": {
                    "type": "string",
                    "description": "Short summary shown to the developer in the approval UI.",
                },
                "sandbox_justification": {
                    "type": "string",
                    "description": "Technical rationale for the automated security reviewer.",
                },
            },
            "required": [
                "command",
                "required_permissions",
                "user_summary",
                "sandbox_justification",
            ],
        },
    },
}

SANDBOX_TOOLS = [EXECUTE_SANDBOXED_COMMAND_TOOL]
