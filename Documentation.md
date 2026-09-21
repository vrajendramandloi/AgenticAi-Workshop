# Agentic AI Projects Documentation

## Project 1: a1_single_agent (Ryan - Tool-Augmented Assistant)

### High-Level Overview
`a1_single_agent` is an autonomous, single-agent assistant built using the Google ADK (`google-adk`) framework. It integrates foundational LLM reasoning with live external tools (physical device/IP geolocation, real-time web search, and browser-based live train tracking), dynamically choosing on the fly whether to answer directly or invoke tools.

### Purpose & Use Cases
- **Location-Aware Assistance**: Resolves queries dependent on the user's physical surroundings (e.g., *"cafes near me"*, *"local weather"*, or *"where am I"*) by automatically detecting local coordinates and city details.
- **Live Information Retrieval**: Searches the web for real-time facts, current news, and post-training data.
- **Real-Time Train Tracking**: Searches and opens the live running status, current position, and station schedules of trains directly in the browser.
- **Multi-Step Tool Chaining**: Autonomously chains tools together (e.g., detecting user location first, then formulating targeted search queries for nearby places and services).
