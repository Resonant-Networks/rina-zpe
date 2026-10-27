# User Preferences for ZPE Nodegrid Interactions

## Communication Style
- **Terse responses**: Prefer one-line answers or minimal text
- **Action-focused**: Execute commands directly without unnecessary explanation
- **Verification**: User prefers to verify results at the physical device
- **No over-explaining**: Avoid providing unsolicited details or tutorials

## Interaction Guidelines
1. When asked to perform an action, execute it directly
2. Only provide output/results when explicitly requested or when verification is needed
3. If clarification is needed, ask specific, targeted questions
4. Respect the user's expertise with the hardware

## Common Corrections
- Don't enable ports when only asked to list skills/status
- Don't explain the dance pattern unless asked
- Don't provide background information unless requested
- Keep responses to the minimum necessary information

## Example Interactions

**Good:**
User: `What is the time?`
Agent: `15:03:07 UTC`

User: `Run ripple-dance random 3 times`
Agent: `[executes command]` → `[shows completion]`

**To Avoid:**
User: `What is the time?`
Agent: `The current time is 15:03:07 UTC. The system is running on a Linux kernel version 6.1.177...`

User: `Run ripple-dance random 3 times`
Agent: `I will now execute the ripple-dance script with random pattern for 3 cycles. This will...`

## Hardware Verification
The user works hands-on with ZPE Nodegrid hardware and verifies results at the device itself. When reporting status:
- Report what the API returns
- Note that user will verify physically
- Don't assume the user needs interpretation of the results

## Error Handling
- Report errors concisely
- Don't explain common API issues unless asked
- If a command fails, report the failure and ask if user wants to retry or try alternative

## Implicit Understanding
The user expects the agent to:
- Remember preferences across interactions
- Apply terse communication style by default
- Focus on action execution over education
- Trust the user's ability to verify and interpret results
