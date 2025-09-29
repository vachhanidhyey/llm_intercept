"""Admin interface endpoints."""

import json
import os
import io
import zstandard as zstd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlmodel import Session, select, col, func

from .database import get_engine
from .models import LLMRequest


router = APIRouter()


def check_admin_password(password: Optional[str] = Query(None)):
    """Verify admin password from environment variable."""
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise HTTPException(status_code=500, detail="Admin password not configured")

    if password != admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    return True


def get_db():
    """Get database session."""
    engine = get_engine()
    with Session(engine) as session:
        yield session


@router.get("/admin", response_class=HTMLResponse)
async def admin_interface(
    password: Optional[str] = Query(None),
    _: bool = Depends(check_admin_password),
):
    """Serve the admin HTML interface."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Intercept - Admin Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
        }
        .stat-card h3 {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
        }
        .filters {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .filter-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        .filter-group {
            display: flex;
            flex-direction: column;
        }
        label {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 5px;
            color: #555;
        }
        input, select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
        }
        button:hover {
            background: #5568d3;
        }
        button.secondary {
            background: #48bb78;
        }
        button.secondary:hover {
            background: #38a169;
        }
        .actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .requests {
            margin-top: 30px;
        }
        .request-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .request-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e2e8f0;
        }
        .request-meta {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .meta-item {
            font-size: 13px;
            color: #666;
        }
        .meta-item strong {
            color: #333;
        }
        .request-content {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
        }
        .json-content {
            font-family: 'Courier New', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 300px;
            overflow-y: auto;
        }
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 30px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .export-options {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 14px;
        }
        .checkbox-label input[type="checkbox"] {
            width: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 LLM Intercept Dashboard</h1>
        <p style="color: #666; margin-bottom: 20px;">Monitor and export your intercepted LLM requests</p>

        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>Total Requests</h3>
                <div class="value" id="totalRequests">-</div>
            </div>
            <div class="stat-card">
                <h3>Unique Models</h3>
                <div class="value" id="uniqueModels">-</div>
            </div>
            <div class="stat-card">
                <h3>Avg Response Time</h3>
                <div class="value" id="avgResponseTime">-</div>
            </div>
        </div>

        <div class="filters">
            <div class="filter-row">
                <div class="filter-group">
                    <label for="startDate">Start Date</label>
                    <input type="datetime-local" id="startDate">
                </div>
                <div class="filter-group">
                    <label for="endDate">End Date</label>
                    <input type="datetime-local" id="endDate">
                </div>
                <div class="filter-group">
                    <label for="modelFilter">Model</label>
                    <select id="modelFilter">
                        <option value="">All Models</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="searchText">Search Text</label>
                    <input type="text" id="searchText" placeholder="Search in messages...">
                </div>
            </div>
            <div class="actions">
                <button onclick="applyFilters()">Apply Filters</button>
                <button onclick="resetFilters()">Reset</button>
                <div class="export-options">
                    <label class="checkbox-label">
                        <input type="checkbox" id="includeSystemPrompt" checked>
                        Include System Prompts
                    </label>
                    <select id="exportFormat" style="padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <option value="parquet" selected>Parquet</option>
                        <option value="jsonl">JSONL.zstd</option>
                    </select>
                    <button class="secondary" onclick="exportData()">Export Dataset</button>
                </div>
            </div>
        </div>

        <div class="requests">
            <h2 style="margin-bottom: 20px;">Recent Requests</h2>
            <div id="requestsList"></div>
            <div class="pagination" id="pagination"></div>
        </div>
    </div>

    <script>
        const API_PASSWORD = new URLSearchParams(window.location.search).get('password');
        let currentPage = 1;
        const pageSize = 20;
        let filters = {};

        async function fetchStats() {
            try {
                const response = await fetch(`/admin/stats?password=${API_PASSWORD}`);
                const data = await response.json();
                document.getElementById('totalRequests').textContent = data.total_requests;
                document.getElementById('uniqueModels').textContent = data.unique_models;
                document.getElementById('avgResponseTime').textContent = data.avg_response_time + 'ms';
            } catch (error) {
                console.error('Error fetching stats:', error);
            }
        }

        async function fetchModels() {
            try {
                const response = await fetch(`/admin/models?password=${API_PASSWORD}`);
                const data = await response.json();
                const select = document.getElementById('modelFilter');
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error fetching models:', error);
            }
        }

        async function fetchRequests(page = 1) {
            document.getElementById('requestsList').innerHTML = '<div class="loading">Loading...</div>';

            try {
                const params = new URLSearchParams({
                    password: API_PASSWORD,
                    skip: (page - 1) * pageSize,
                    limit: pageSize,
                    ...filters
                });

                const response = await fetch(`/admin/requests?${params}`);
                const data = await response.json();

                displayRequests(data.requests);
                displayPagination(data.total, page);
            } catch (error) {
                console.error('Error fetching requests:', error);
                document.getElementById('requestsList').innerHTML = '<div class="loading">Error loading requests</div>';
            }
        }

        function displayRequests(requests) {
            const container = document.getElementById('requestsList');

            if (requests.length === 0) {
                container.innerHTML = '<div class="loading">No requests found</div>';
                return;
            }

            container.innerHTML = requests.map(req => {
                const messages = JSON.parse(req.messages);
                const response = req.response ? JSON.parse(req.response) : null;
                const toolCalls = req.tool_calls ? JSON.parse(req.tool_calls) : null;
                const statusColor = req.status === 'ok' ? '#48bb78' : '#f56565';
                const statusBadge = `<div class="meta-item" style="color: ${statusColor}; font-weight: bold;"><strong>STATUS:</strong> ${req.status.toUpperCase()}</div>`;

                return `
                    <div class="request-card" style="border-left: 4px solid ${statusColor};">
                        <div class="request-header">
                            <div class="request-meta">
                                <div class="meta-item"><strong>ID:</strong> ${req.id}</div>
                                <div class="meta-item"><strong>Model:</strong> ${req.model}</div>
                                <div class="meta-item"><strong>Time:</strong> ${new Date(req.timestamp).toLocaleString()}</div>
                                <div class="meta-item"><strong>Response Time:</strong> ${req.response_time_ms || 'N/A'}ms</div>
                                ${statusBadge}
                                ${req.stream ? '<div class="meta-item" style="color: #667eea;"><strong>STREAM</strong></div>' : ''}
                                ${toolCalls ? '<div class="meta-item" style="color: #9f7aea;"><strong>HAS TOOL CALLS</strong></div>' : ''}
                            </div>
                        </div>
                        ${req.error ? `<div style="background: #fed7d7; color: #c53030; padding: 10px; border-radius: 4px; margin: 10px 0;"><strong>Error:</strong> ${req.error}</div>` : ''}
                        <details>
                            <summary style="cursor: pointer; font-weight: 600; margin-bottom: 10px;">View Messages (${messages.length})</summary>
                            <div class="request-content">
                                <div class="json-content">${JSON.stringify(messages, null, 2)}</div>
                            </div>
                        </details>
                        ${toolCalls ? `
                        <details style="margin-top: 10px;">
                            <summary style="cursor: pointer; font-weight: 600; margin-bottom: 10px;">View Tool Calls</summary>
                            <div class="request-content">
                                <div class="json-content">${JSON.stringify(toolCalls, null, 2)}</div>
                            </div>
                        </details>
                        ` : ''}
                        ${response ? `
                        <details style="margin-top: 10px;">
                            <summary style="cursor: pointer; font-weight: 600; margin-bottom: 10px;">View Raw Response</summary>
                            <div class="request-content">
                                <div class="json-content">${JSON.stringify(response, null, 2)}</div>
                            </div>
                        </details>
                        ` : ''}
                    </div>
                `;
            }).join('');
        }

        function displayPagination(total, currentPage) {
            const totalPages = Math.ceil(total / pageSize);
            const container = document.getElementById('pagination');

            if (totalPages <= 1) {
                container.innerHTML = '';
                return;
            }

            let html = '';

            if (currentPage > 1) {
                html += `<button onclick="changePage(${currentPage - 1})">Previous</button>`;
            }

            html += `<span style="padding: 10px;">Page ${currentPage} of ${totalPages}</span>`;

            if (currentPage < totalPages) {
                html += `<button onclick="changePage(${currentPage + 1})">Next</button>`;
            }

            container.innerHTML = html;
        }

        function changePage(page) {
            currentPage = page;
            fetchRequests(page);
        }

        function applyFilters() {
            filters = {};

            const startDate = document.getElementById('startDate').value;
            if (startDate) filters.start_date = startDate;

            const endDate = document.getElementById('endDate').value;
            if (endDate) filters.end_date = endDate;

            const model = document.getElementById('modelFilter').value;
            if (model) filters.model = model;

            const search = document.getElementById('searchText').value;
            if (search) filters.search = search;

            currentPage = 1;
            fetchRequests(1);
        }

        function resetFilters() {
            document.getElementById('startDate').value = '';
            document.getElementById('endDate').value = '';
            document.getElementById('modelFilter').value = '';
            document.getElementById('searchText').value = '';
            filters = {};
            currentPage = 1;
            fetchRequests(1);
        }

        async function exportData() {
            try {
                const includeSystemPrompt = document.getElementById('includeSystemPrompt').checked;
                const exportFormat = document.getElementById('exportFormat').value;
                const params = new URLSearchParams({
                    password: API_PASSWORD,
                    include_system_prompt: includeSystemPrompt,
                    format: exportFormat,
                    ...filters
                });

                window.location.href = `/admin/export?${params}`;
            } catch (error) {
                console.error('Error exporting data:', error);
                alert('Error exporting data');
            }
        }

        // Initialize
        fetchStats();
        fetchModels();
        fetchRequests(1);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@router.get("/admin/stats")
async def get_stats(
    db: Session = Depends(get_db),
    _: bool = Depends(check_admin_password),
):
    """Get statistics about intercepted requests."""
    total_requests = db.exec(select(func.count(LLMRequest.id))).one()
    unique_models = db.exec(select(func.count(func.distinct(LLMRequest.model)))).one()

    avg_response_time = db.exec(
        select(func.avg(LLMRequest.response_time_ms)).where(LLMRequest.response_time_ms.isnot(None))
    ).one()

    return {
        "total_requests": total_requests,
        "unique_models": unique_models,
        "avg_response_time": int(avg_response_time) if avg_response_time else 0,
    }


@router.get("/admin/models")
async def get_models(
    db: Session = Depends(get_db),
    _: bool = Depends(check_admin_password),
):
    """Get list of unique models."""
    models = db.exec(select(LLMRequest.model).distinct()).all()
    return {"models": sorted(models)}


@router.get("/admin/requests")
async def get_requests(
    skip: int = 0,
    limit: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    model: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(check_admin_password),
):
    """Get paginated list of requests with optional filtering."""
    query = select(LLMRequest)

    # Apply filters
    if start_date:
        query = query.where(LLMRequest.timestamp >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(LLMRequest.timestamp <= datetime.fromisoformat(end_date))
    if model:
        query = query.where(LLMRequest.model == model)
    if search:
        query = query.where(col(LLMRequest.messages).contains(search))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.exec(count_query).one()

    # Get paginated results
    query = query.order_by(LLMRequest.timestamp.desc()).offset(skip).limit(limit)
    requests = db.exec(query).all()

    return {
        "requests": [
            {
                "id": req.id,
                "timestamp": req.timestamp.isoformat(),
                "model": req.model,
                "messages": req.messages,
                "response": req.response,
                "response_time_ms": req.response_time_ms,
                "stream": req.stream,
                "status": req.status,
                "error": req.error,
                "tool_calls": req.tool_calls,
            }
            for req in requests
        ],
        "total": total,
    }


@router.get("/admin/export")
async def export_requests(
    include_system_prompt: bool = True,
    format: str = "jsonl",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    model: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(check_admin_password),
):
    """Export filtered requests as JSONL.zstd or Parquet file. Only exports requests with status='ok'."""
    query = select(LLMRequest)

    # IMPORTANT: Only export OK responses
    query = query.where(LLMRequest.status == "ok")

    # Apply filters
    if start_date:
        query = query.where(LLMRequest.timestamp >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(LLMRequest.timestamp <= datetime.fromisoformat(end_date))
    if model:
        query = query.where(LLMRequest.model == model)
    if search:
        query = query.where(col(LLMRequest.messages).contains(search))

    query = query.order_by(LLMRequest.timestamp.desc())
    requests = db.exec(query).all()

    # Prepare data entries
    entries = []
    for req in requests:
        messages = json.loads(req.messages)

        # Filter out system prompts if requested
        if not include_system_prompt:
            messages = [msg for msg in messages if msg.get("role") != "system"]

        entry = {
            "messages": messages,
            "model": req.model,
            "timestamp": req.timestamp.isoformat(),
        }

        # Add tool_calls if present
        if req.tool_calls:
            entry["tool_calls"] = json.loads(req.tool_calls)

        entries.append(entry)

    # Create filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if format == "parquet":
        # Convert to Parquet
        # Flatten the data for Parquet - store messages and tool_calls as JSON strings
        parquet_data = {
            "messages": [json.dumps(e["messages"]) for e in entries],
            "model": [e["model"] for e in entries],
            "timestamp": [e["timestamp"] for e in entries],
            "tool_calls": [json.dumps(e.get("tool_calls")) if e.get("tool_calls") else None for e in entries],
        }

        table = pa.Table.from_pydict(parquet_data)

        # Write to buffer
        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)

        filename = f"llm_intercept_export_{timestamp}.parquet"

        return Response(
            content=buffer.getvalue(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )
    else:
        # Create JSONL content
        jsonl_lines = [json.dumps(entry) for entry in entries]
        jsonl_content = "\n".join(jsonl_lines).encode("utf-8")

        # Compress with zstd
        compressor = zstd.ZstdCompressor()
        compressed_content = compressor.compress(jsonl_content)

        filename = f"llm_intercept_export_{timestamp}.jsonl.zst"

        return Response(
            content=compressed_content,
            media_type="application/zstd",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )