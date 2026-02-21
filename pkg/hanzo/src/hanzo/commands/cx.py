"""Hanzo CX - Customer experience and operations CLI.

Support, CRM, and ERP.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from .base import check_response, service_request
from ..utils.output import console

SERVICE_URL = os.getenv("HANZO_CX_URL", "https://cx.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(SERVICE_URL, method, path, **kwargs)


@click.group(name="cx")
def cx_group():
    """Hanzo CX - Customer experience and operations.

    \b
    Support (Inbox):
      hanzo cx inbox list          # List conversations
      hanzo cx inbox assign        # Assign conversation
      hanzo cx inbox reply         # Reply to conversation

    \b
    CRM:
      hanzo cx contacts list       # List contacts
      hanzo cx deals list          # List deals
      hanzo cx pipelines list      # List pipelines

    \b
    ERP:
      hanzo cx invoices list       # List invoices
      hanzo cx orders list         # List orders
    """
    pass


# ============================================================================
# Inbox (Support)
# ============================================================================


@cx_group.group()
def inbox():
    """Manage support inbox."""
    pass


@inbox.command(name="list")
@click.option("--status", type=click.Choice(["open", "pending", "resolved", "all"]), default="open")
@click.option("--channel", type=click.Choice(["email", "chat", "social", "all"]), default="all")
@click.option("--limit", "-n", default=50, help="Max results")
def inbox_list(status: str, channel: str, limit: int):
    """List inbox conversations."""
    params: dict = {"limit": limit}
    if status != "all":
        params["status"] = status
    if channel != "all":
        params["channel"] = channel
    resp = _request("get", "/v1/inbox/conversations", params=params)
    data = check_response(resp)

    table = Table(title="Support Inbox", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Subject", style="white")
    table.add_column("Channel", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Assignee", style="dim")
    table.add_column("Updated", style="dim")

    for c in data.get("conversations", []):
        st = c.get("status", "open")
        st_style = {"open": "yellow", "pending": "cyan", "resolved": "green"}.get(st, "white")
        table.add_row(
            c.get("id", "")[:12],
            c.get("subject", ""),
            c.get("channel", ""),
            f"[{st_style}]{st}[/{st_style}]",
            c.get("assignee", "unassigned"),
            c.get("updated_at", ""),
        )

    console.print(table)


@inbox.command(name="show")
@click.argument("conversation_id")
def inbox_show(conversation_id: str):
    """Show conversation details."""
    resp = _request("get", f"/v1/inbox/conversations/{conversation_id}")
    data = check_response(resp)

    info = (
        f"[cyan]ID:[/cyan] {data.get('id', conversation_id)}\n"
        f"[cyan]Subject:[/cyan] {data.get('subject', 'N/A')}\n"
        f"[cyan]Customer:[/cyan] {data.get('customer_email', 'N/A')}\n"
        f"[cyan]Status:[/cyan] {data.get('status', 'N/A')}\n"
        f"[cyan]Channel:[/cyan] {data.get('channel', 'N/A')}\n"
        f"[cyan]Messages:[/cyan] {data.get('message_count', 0)}\n"
        f"[cyan]Assignee:[/cyan] {data.get('assignee', 'unassigned')}"
    )
    console.print(Panel(info, title="Conversation", border_style="cyan"))

    messages = data.get("messages", [])
    if messages:
        console.print()
        for msg in messages:
            sender = msg.get("sender", "unknown")
            style = "cyan" if msg.get("is_agent") else "white"
            console.print(f"[{style}]{sender}[/{style}] [dim]{msg.get('created_at', '')}[/dim]")
            console.print(f"  {msg.get('body', '')}")
            console.print()


@inbox.command(name="assign")
@click.argument("conversation_id")
@click.option("--agent", "-a", required=True, help="Agent email or ID")
def inbox_assign(conversation_id: str, agent: str):
    """Assign conversation to agent."""
    resp = _request("post", f"/v1/inbox/conversations/{conversation_id}/assign", json={"agent": agent})
    check_response(resp)
    console.print(f"[green]✓[/green] Conversation assigned to {agent}")


@inbox.command(name="reply")
@click.argument("conversation_id")
@click.option("--message", "-m", prompt=True, help="Reply message")
def inbox_reply(conversation_id: str, message: str):
    """Reply to a conversation."""
    resp = _request("post", f"/v1/inbox/conversations/{conversation_id}/reply", json={"body": message})
    check_response(resp)
    console.print(f"[green]✓[/green] Reply sent")


@inbox.command(name="resolve")
@click.argument("conversation_id")
def inbox_resolve(conversation_id: str):
    """Mark conversation as resolved."""
    resp = _request("post", f"/v1/inbox/conversations/{conversation_id}/resolve")
    check_response(resp)
    console.print(f"[green]✓[/green] Conversation resolved")


@inbox.command(name="reopen")
@click.argument("conversation_id")
def inbox_reopen(conversation_id: str):
    """Reopen a resolved conversation."""
    resp = _request("post", f"/v1/inbox/conversations/{conversation_id}/reopen")
    check_response(resp)
    console.print(f"[green]✓[/green] Conversation reopened")


# ============================================================================
# Contacts (CRM)
# ============================================================================


@cx_group.group()
def contacts():
    """Manage CRM contacts."""
    pass


@contacts.command(name="list")
@click.option("--search", "-s", help="Search contacts")
@click.option("--limit", "-n", default=50, help="Max results")
def contacts_list(search: str, limit: int):
    """List contacts."""
    params: dict = {"limit": limit}
    if search:
        params["search"] = search
    resp = _request("get", "/v1/contacts", params=params)
    data = check_response(resp)

    table = Table(title="Contacts", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Email", style="white")
    table.add_column("Company", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")

    for c in data.get("contacts", []):
        table.add_row(
            c.get("name", ""),
            c.get("email", ""),
            c.get("company", ""),
            c.get("status", "active"),
            c.get("created_at", ""),
        )

    console.print(table)


@contacts.command(name="show")
@click.argument("contact_id")
def contacts_show(contact_id: str):
    """Show contact details."""
    resp = _request("get", f"/v1/contacts/{contact_id}")
    data = check_response(resp)

    info = (
        f"[cyan]Name:[/cyan] {data.get('name', 'N/A')}\n"
        f"[cyan]Email:[/cyan] {data.get('email', 'N/A')}\n"
        f"[cyan]Company:[/cyan] {data.get('company', 'N/A')}\n"
        f"[cyan]Phone:[/cyan] {data.get('phone', 'N/A')}\n"
        f"[cyan]Deals:[/cyan] {data.get('deal_count', 0)} (${data.get('deal_value', 0):,.0f})"
    )
    console.print(Panel(info, title="Contact Details", border_style="cyan"))


@contacts.command(name="create")
@click.option("--name", "-n", prompt=True, help="Contact name")
@click.option("--email", "-e", prompt=True, help="Email")
@click.option("--company", "-c", help="Company")
@click.option("--phone", "-p", help="Phone")
def contacts_create(name: str, email: str, company: str, phone: str):
    """Create a contact."""
    payload: dict = {"name": name, "email": email}
    if company:
        payload["company"] = company
    if phone:
        payload["phone"] = phone
    resp = _request("post", "/v1/contacts", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Contact '{name}' created")


@contacts.command(name="update")
@click.argument("contact_id")
@click.option("--name", "-n", help="Contact name")
@click.option("--email", "-e", help="Email")
@click.option("--company", "-c", help="Company")
@click.option("--phone", "-p", help="Phone")
def contacts_update(contact_id: str, name: str, email: str, company: str, phone: str):
    """Update a contact."""
    payload: dict = {}
    if name:
        payload["name"] = name
    if email:
        payload["email"] = email
    if company:
        payload["company"] = company
    if phone:
        payload["phone"] = phone
    if not payload:
        raise click.ClickException("Provide at least one field to update")
    resp = _request("patch", f"/v1/contacts/{contact_id}", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Contact updated")


@contacts.command(name="delete")
@click.argument("contact_id")
def contacts_delete(contact_id: str):
    """Delete a contact."""
    resp = _request("delete", f"/v1/contacts/{contact_id}")
    check_response(resp)
    console.print(f"[green]✓[/green] Contact deleted")


# ============================================================================
# Deals (CRM)
# ============================================================================


@cx_group.group()
def deals():
    """Manage CRM deals."""
    pass


@deals.command(name="list")
@click.option("--pipeline", "-p", help="Filter by pipeline")
@click.option("--stage", "-s", help="Filter by stage")
@click.option("--limit", "-n", default=50, help="Max results")
def deals_list(pipeline: str, stage: str, limit: int):
    """List deals."""
    params: dict = {"limit": limit}
    if pipeline:
        params["pipeline"] = pipeline
    if stage:
        params["stage"] = stage
    resp = _request("get", "/v1/deals", params=params)
    data = check_response(resp)

    table = Table(title="Deals", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Stage", style="white")
    table.add_column("Contact", style="dim")
    table.add_column("Close Date", style="dim")

    for d in data.get("deals", []):
        table.add_row(
            d.get("name", ""),
            f"${d.get('value', 0):,.0f}",
            d.get("stage", ""),
            d.get("contact_name", ""),
            d.get("close_date", ""),
        )

    console.print(table)


@deals.command(name="show")
@click.argument("deal_id")
def deals_show(deal_id: str):
    """Show deal details."""
    resp = _request("get", f"/v1/deals/{deal_id}")
    data = check_response(resp)

    info = (
        f"[cyan]Deal:[/cyan] {data.get('name', 'N/A')}\n"
        f"[cyan]Value:[/cyan] ${data.get('value', 0):,.0f}\n"
        f"[cyan]Stage:[/cyan] {data.get('stage', 'N/A')}\n"
        f"[cyan]Pipeline:[/cyan] {data.get('pipeline', 'default')}\n"
        f"[cyan]Contact:[/cyan] {data.get('contact_name', 'N/A')}\n"
        f"[cyan]Close Date:[/cyan] {data.get('close_date', 'N/A')}"
    )
    console.print(Panel(info, title="Deal Details", border_style="cyan"))


@deals.command(name="create")
@click.option("--name", "-n", prompt=True, help="Deal name")
@click.option("--value", "-v", type=float, prompt=True, help="Deal value")
@click.option("--contact", "-c", required=True, help="Contact ID")
@click.option("--pipeline", "-p", default="default", help="Pipeline")
@click.option("--stage", "-s", help="Initial stage")
def deals_create(name: str, value: float, contact: str, pipeline: str, stage: str):
    """Create a deal."""
    payload: dict = {"name": name, "value": value, "contact_id": contact, "pipeline": pipeline}
    if stage:
        payload["stage"] = stage
    resp = _request("post", "/v1/deals", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Deal '{name}' created (${value:,.0f})")


@deals.command(name="move")
@click.argument("deal_id")
@click.option("--stage", "-s", required=True, help="Target stage")
def deals_move(deal_id: str, stage: str):
    """Move deal to a stage."""
    resp = _request("patch", f"/v1/deals/{deal_id}", json={"stage": stage})
    check_response(resp)
    console.print(f"[green]✓[/green] Deal moved to '{stage}'")


@deals.command(name="delete")
@click.argument("deal_id")
def deals_delete(deal_id: str):
    """Delete a deal."""
    resp = _request("delete", f"/v1/deals/{deal_id}")
    check_response(resp)
    console.print(f"[green]✓[/green] Deal deleted")


# ============================================================================
# Pipelines (CRM)
# ============================================================================


@cx_group.group()
def pipelines():
    """Manage sales pipelines."""
    pass


@pipelines.command(name="list")
def pipelines_list():
    """List pipelines."""
    resp = _request("get", "/v1/pipelines")
    data = check_response(resp)

    table = Table(title="Pipelines", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Stages", style="white")
    table.add_column("Deals", style="dim")
    table.add_column("Value", style="green")

    for p in data.get("pipelines", []):
        stages = " → ".join(p.get("stages", []))
        table.add_row(
            p.get("name", ""),
            stages,
            str(p.get("deal_count", 0)),
            f"${p.get('total_value', 0):,.0f}",
        )

    console.print(table)


@pipelines.command(name="create")
@click.option("--name", "-n", prompt=True, help="Pipeline name")
@click.option("--stages", "-s", required=True, help="Comma-separated stages")
def pipelines_create(name: str, stages: str):
    """Create a pipeline."""
    stage_list = [s.strip() for s in stages.split(",")]
    resp = _request("post", "/v1/pipelines", json={"name": name, "stages": stage_list})
    check_response(resp)
    console.print(f"[green]✓[/green] Pipeline '{name}' created")


@pipelines.command(name="delete")
@click.argument("name")
def pipelines_delete(name: str):
    """Delete a pipeline."""
    resp = _request("delete", f"/v1/pipelines/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Pipeline '{name}' deleted")


# ============================================================================
# Invoices (ERP)
# ============================================================================


@cx_group.group()
def invoices():
    """Manage invoices."""
    pass


@invoices.command(name="list")
@click.option("--status", type=click.Choice(["draft", "sent", "paid", "overdue", "all"]), default="all")
@click.option("--limit", "-n", default=50, help="Max results")
def invoices_list(status: str, limit: int):
    """List invoices."""
    params: dict = {"limit": limit}
    if status != "all":
        params["status"] = status
    resp = _request("get", "/v1/invoices", params=params)
    data = check_response(resp)

    table = Table(title="Invoices", box=box.ROUNDED)
    table.add_column("Number", style="cyan")
    table.add_column("Customer", style="white")
    table.add_column("Amount", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Due Date", style="dim")

    for inv in data.get("invoices", []):
        st = inv.get("status", "draft")
        st_style = {"paid": "green", "overdue": "red", "sent": "cyan"}.get(st, "yellow")
        table.add_row(
            inv.get("number", ""),
            inv.get("customer_name", ""),
            f"${inv.get('amount', 0):,.2f}",
            f"[{st_style}]{st}[/{st_style}]",
            inv.get("due_date", ""),
        )

    console.print(table)


@invoices.command(name="create")
@click.option("--customer", "-c", required=True, help="Customer ID")
@click.option("--amount", "-a", type=float, required=True, help="Amount")
@click.option("--due", "-d", help="Due date (YYYY-MM-DD)")
@click.option("--items", help="Line items JSON")
def invoices_create(customer: str, amount: float, due: str, items: str):
    """Create an invoice."""
    payload: dict = {"customer_id": customer, "amount": amount}
    if due:
        payload["due_date"] = due
    if items:
        payload["items"] = json.loads(items)
    resp = _request("post", "/v1/invoices", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Invoice {data.get('number', '')} created for ${amount:,.2f}")


@invoices.command(name="send")
@click.argument("invoice_number")
def invoices_send(invoice_number: str):
    """Send an invoice."""
    resp = _request("post", f"/v1/invoices/{invoice_number}/send")
    check_response(resp)
    console.print(f"[green]✓[/green] Invoice {invoice_number} sent")


@invoices.command(name="mark-paid")
@click.argument("invoice_number")
@click.option("--payment-method", help="Payment method used")
def invoices_mark_paid(invoice_number: str, payment_method: str):
    """Mark invoice as paid."""
    payload: dict = {}
    if payment_method:
        payload["payment_method"] = payment_method
    resp = _request("post", f"/v1/invoices/{invoice_number}/pay", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Invoice {invoice_number} marked as paid")


@invoices.command(name="delete")
@click.argument("invoice_number")
def invoices_delete(invoice_number: str):
    """Delete an invoice."""
    resp = _request("delete", f"/v1/invoices/{invoice_number}")
    check_response(resp)
    console.print(f"[green]✓[/green] Invoice {invoice_number} deleted")


# ============================================================================
# Orders (ERP)
# ============================================================================


@cx_group.group()
def orders():
    """Manage orders."""
    pass


@orders.command(name="list")
@click.option("--status", type=click.Choice(["pending", "processing", "shipped", "delivered", "all"]), default="all")
@click.option("--limit", "-n", default=50, help="Max results")
def orders_list(status: str, limit: int):
    """List orders."""
    params: dict = {"limit": limit}
    if status != "all":
        params["status"] = status
    resp = _request("get", "/v1/orders", params=params)
    data = check_response(resp)

    table = Table(title="Orders", box=box.ROUNDED)
    table.add_column("Order #", style="cyan")
    table.add_column("Customer", style="white")
    table.add_column("Total", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Date", style="dim")

    for o in data.get("orders", []):
        st = o.get("status", "pending")
        st_style = {"delivered": "green", "shipped": "cyan", "processing": "yellow"}.get(st, "white")
        table.add_row(
            o.get("order_number", ""),
            o.get("customer_name", ""),
            f"${o.get('total', 0):,.2f}",
            f"[{st_style}]{st}[/{st_style}]",
            o.get("created_at", ""),
        )

    console.print(table)


@orders.command(name="show")
@click.argument("order_id")
def orders_show(order_id: str):
    """Show order details."""
    resp = _request("get", f"/v1/orders/{order_id}")
    data = check_response(resp)

    info = (
        f"[cyan]Order #:[/cyan] {data.get('order_number', order_id)}\n"
        f"[cyan]Customer:[/cyan] {data.get('customer_name', 'N/A')}\n"
        f"[cyan]Total:[/cyan] ${data.get('total', 0):,.2f}\n"
        f"[cyan]Status:[/cyan] {data.get('status', 'N/A')}\n"
        f"[cyan]Items:[/cyan] {data.get('item_count', 0)}"
    )
    console.print(Panel(info, title="Order Details", border_style="cyan"))

    items = data.get("items", [])
    if items:
        table = Table(title="Order Items", box=box.ROUNDED)
        table.add_column("Product", style="white")
        table.add_column("Qty", style="dim")
        table.add_column("Price", style="green")
        table.add_column("Subtotal", style="green")

        for item in items:
            table.add_row(
                item.get("product_name", ""),
                str(item.get("quantity", 0)),
                f"${item.get('unit_price', 0):,.2f}",
                f"${item.get('subtotal', 0):,.2f}",
            )

        console.print(table)


@orders.command(name="update-status")
@click.argument("order_id")
@click.option("--status", "-s", type=click.Choice(["processing", "shipped", "delivered"]), required=True)
@click.option("--tracking", "-t", help="Tracking number")
def orders_update_status(order_id: str, status: str, tracking: str):
    """Update order status."""
    payload: dict = {"status": status}
    if tracking:
        payload["tracking_number"] = tracking
    resp = _request("patch", f"/v1/orders/{order_id}", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Order {order_id} status updated to '{status}'")
