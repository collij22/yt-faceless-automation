# MCP Setup (Claude Code)

This guide configures Firecrawl MCP, n8n MCP, and Ref MCP for this project.

> Always consult Ref MCP to fetch latest docs for tools you call from subagents.

## 1) Firecrawl MCP
- Repo: https://github.com/firecrawl/firecrawl-mcp-server
- Purpose: web search + scraping with extraction of headings, summaries, and links.
- Steps:
  1. Install per repo README.
  2. Add MCP server to Claude Code settings.
  3. Verify tools are visible in `/agents` tool selection.

## 2) n8n MCP
- Listing: https://lobehub.com/mcp/illuminaresolutions-n8n-mcp-server
- Purpose: expose n8n workflows as callable tools from Claude.
- Steps:
  1. Install per listing instructions.
  2. Configure authentication to your n8n instance.
  3. Expose TTS and Upload workflows as tools or keep webhook endpoints.

## 3) Ref MCP
- Purpose: query latest documentation for referenced platforms (YouTube API, n8n nodes, FFmpeg flags) to ensure current best practices.
- Steps:
  1. Install Ref MCP.
  2. Confirm it appears in the `/agents` tool picker.

## 4) Tool Access in Subagents
- If omitted, subagents inherit all tools. You can explicitly restrict per subagent by adding `tools:` in the frontmatter.

## 5) YouTube via n8n
- Docs: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.youtube/
- Configure OAuth credentials in n8n. Test upload with a small private video.
