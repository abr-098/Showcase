# Jenkins Server MCP


I have created an extended MCP with much better tools for Infra Automation (vide-coding)

A Model Context Protocol (MCP) server that provides tools for interacting with Jenkins CI/CD servers. This server enables AI assistants to check build statuses, trigger builds, retrieve build logs, and execute Ansible ad-hoc commands through a standardized interface.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/abr-098/jenkinsmcp.git
cd jenkinsmcp
```

2. Install dependencies:
```bash
npm install
```

3. Build the project:
```bash
npm run build
```

## Configuration

The server requires the following environment variables:

### Required Variables
- `JENKINS_URL`: The URL of your Jenkins server
- `JENKINS_USER`: Jenkins username for authentication
- `JENKINS_TOKEN`: Jenkins API token for authentication

### Security Configuration (Optional)
- `JENKINS_RESTRICTED_COMMANDS`: Comma-separated list of blocked commands (default: `init 6,reboot,shutdown`)
- `JENKINS_ENABLE_COMMAND_VALIDATION`: Enable/disable command validation (default: `true`)
- `JENKINS_ALLOWED_ANSIBLE_MODULES`: Comma-separated list of allowed Ansible modules (default: `shell,command,systemd,service,copy,file,template,yum,apt,git,ping,setup,user,group,cron,mount,unarchive,uri,get_url,lineinfile,replace,blockinfile,stat,debug,set_fact,include_vars,wait_for,pause,fail,assert`)
- `JENKINS_DEFAULT_SSH_USER`: Default SSH username for Ansible connections (default: `ec2-user`)
- `JENKINS_ENABLE_INVENTORY_VALIDATION`: Enable/disable inventory format validation (default: `true`)

### Operational Configuration (Optional)
- `JENKINS_DEFAULT_TIMEOUT`: Default timeout in milliseconds (default: `300000` - 5 minutes)
- `JENKINS_MAX_TIMEOUT`: Maximum allowed timeout in milliseconds (default: `1800000` - 30 minutes)
- `JENKINS_POLLING_INTERVAL`: Build status polling interval in milliseconds (default: `5000` - 5 seconds)
- `JENKINS_JOB_START_WAIT`: Wait time before checking job status in milliseconds (default: `2000` - 2 seconds)

Configure these in your MCP settings file:

### For Claude Desktop

MacOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "jenkins-server": {
      "command": "node",
      "args": ["/path/to/jenkinsmcp/build/index.js"],
      "env": {
        "JENKINS_URL": "https://your-jenkins-server.com",
        "JENKINS_USER": "your-username",
        "JENKINS_TOKEN": "your-api-token",
        "JENKINS_RESTRICTED_COMMANDS": "init 6,reboot,shutdown,rm -rf",
        "JENKINS_ALLOWED_ANSIBLE_MODULES": "shell,command,systemd,ping,setup",
        "JENKINS_DEFAULT_SSH_USER": "ansible-user",
        "JENKINS_DEFAULT_TIMEOUT": "300000",
        "JENKINS_MAX_TIMEOUT": "1800000"
      }
    }
  }
}
```

## Tools and Usage

### 1. Get Build Status

Get the status of a Jenkins build:

```typescript
// Example usage
const result = await mcpClient.useTool("jenkins-server", "get_build_status", {
  jobPath: "view/xxx_debug",
  buildNumber: "lastBuild"  // Optional, defaults to lastBuild
});
```

Input Schema:
```json
{
  "jobPath": "string",  // Path to Jenkins job
  "buildNumber": "string"  // Optional, build number or "lastBuild"
}
```

### 2. Trigger Build

Trigger a new Jenkins build with or without parameters:

```typescript
// Example usage with parameters
const result = await mcpClient.useTool("jenkins-server", "trigger_build", {
  jobPath: "view/xxx_debug",
  parameters: {
    BRANCH: "main",
    BUILD_TYPE: "debug"
  }
});

// Example usage without parameters
const result = await mcpClient.useTool("jenkins-server", "trigger_build", {
  jobPath: "view/xxx_debug"
});
```

Input Schema:
```json
{
  "jobPath": "string",  // Path to Jenkins job
  "parameters": {       // Optional, build parameters as key-value pairs
    // Build parameters
  }
}
```

### 3. Get Build Log

Retrieve the console output of a Jenkins build:

```typescript
// Example usage
const result = await mcpClient.useTool("jenkins-server", "get_build_log", {
  jobPath: "view/xxx_debug",
  buildNumber: "lastBuild"
});
```

Input Schema:
```json
{
  "jobPath": "string",  // Path to Jenkins job
  "buildNumber": "string"  // Build number or "lastBuild"
}
```

### 4. Run Ansible Ad-hoc Commands

Execute ad-hoc Ansible commands on target servers with dynamic inventory. This tool supports command validation, timeout handling, job cancellation, and continuation capabilities.

```typescript
// Example: Execute shell command on multiple servers
const result = await mcpClient.useTool("jenkins-server", "run_ansible_adhoc", {
  jobPath: "ansible-job",
  inventory: "192.168.1.10,192.168.1.11,web-servers",
  command: "systemctl status nginx",
  module: "shell",
  become: true,
  ssh_user: "ansible",
  timeout: 300000
});

// Example: Continue waiting for a running job
const result = await mcpClient.useTool("jenkins-server", "run_ansible_adhoc", {
  jobPath: "ansible-job",
  buildNumber: "123",
  continue_waiting: true,
  timeout: 300000
});

// Example: Cancel a running job
const result = await mcpClient.useTool("jenkins-server", "run_ansible_adhoc", {
  jobPath: "ansible-job",
  buildNumber: "123",
  cancel_job: true
});
```

Input Schema:
```json
{
  "jobPath": "string",         // Path to Jenkins job that runs Ansible
  "inventory": "string",       // Target servers (comma-separated IPs, hostnames, or groups)
  "command": "string",         // Command to execute on target servers
  "module": "string",          // Ansible module (shell, command, systemd, etc.)
  "become": "boolean",         // Optional, use sudo for command execution
  "ssh_user": "string",        // Optional, SSH username (defaults to ec2-user)
  "timeout": "number",         // Optional, timeout in milliseconds (defaults to 300000ms/5min)
  "continue_waiting": "boolean", // Optional, continue waiting for existing job
  "buildNumber": "string",     // Optional, build number for continuation/cancellation
  "cancel_job": "boolean"      // Optional, cancel running job
}
```

**Security Features:**
- Restricted commands are blocked (init 6, reboot, shutdown)
- Command validation before execution
- Timeout protection to prevent hanging jobs

**Response Handling:**
- Automatic parsing of Ansible output from Jenkins console logs
- Support for job continuation when timeout occurs
- Graceful job cancellation capabilities

## Security Considerations

This MCP server includes several security features that can be configured through environment variables:

### Command Validation
- **Purpose**: Prevent execution of dangerous commands
- **Configuration**: `JENKINS_RESTRICTED_COMMANDS` - comma-separated list of blocked commands
- **Default**: Blocks `init 6`, `reboot`, and `shutdown`
- **Disable**: Set `JENKINS_ENABLE_COMMAND_VALIDATION=false` (not recommended)

### Ansible Module Restrictions
- **Purpose**: Limit which Ansible modules can be used
- **Configuration**: `JENKINS_ALLOWED_ANSIBLE_MODULES` - comma-separated list of allowed modules
- **Default**: Includes common safe modules like `shell`, `command`, `systemd`, etc.
- **Recommendation**: Customize based on your security requirements

### Inventory Validation
- **Purpose**: Validate inventory format to prevent injection attacks
- **Configuration**: `JENKINS_ENABLE_INVENTORY_VALIDATION` - enable/disable validation
- **Default**: Enabled - validates IP addresses, hostnames, and group names
- **Disable**: Set `JENKINS_ENABLE_INVENTORY_VALIDATION=false` (not recommended)

### Timeout Limits
- **Purpose**: Prevent resource exhaustion from long-running jobs
- **Configuration**: `JENKINS_MAX_TIMEOUT` - maximum allowed timeout
- **Default**: 30 minutes (1800000ms)
- **Recommendation**: Set based on your typical job duration requirements

### Best Practices
1. **Use dedicated Jenkins user**: Create a Jenkins user with minimal required permissions
2. **Restrict API token scope**: Use Jenkins API tokens with limited scope when possible
3. **Monitor usage**: Review Jenkins job logs regularly for suspicious activity
4. **Network security**: Ensure Jenkins server is properly secured and accessible only from authorized networks
5. **Regular updates**: Keep Jenkins and this MCP server updated with security patches

## Development

For development with auto-rebuild:
```bash
npm run watch
```

### Debugging

Since MCP servers communicate over stdio, you can use the MCP Inspector for debugging:

```bash
npm run inspector
```

This will provide a URL to access debugging tools in your browser.

## Thanks

Thanks AIMCP(https://www.aimcp.info).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
