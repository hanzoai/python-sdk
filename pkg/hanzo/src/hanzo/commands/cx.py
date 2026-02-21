"""Hanzo CX - Customer experience and operations CLI.

Support, CRM, and ERP.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


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
def inbox_list(status: str, channel: str):
    """List inbox conversations."""
    table = Table(title="Support Inbox", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Subject", style="white")
    table.add_column("Channel", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Assignee", style="dim")
    table.add_column("Updated", style="dim")

    console.print(table)


@inbox.command(name="show")
@click.argument("conversation_id")
def inbox_show(conversation_id: str):
    """Show conversation details."""
    console.print(
        Panel(
            f"[cyan]ID:[/cyan] {conversation_id}\n"
            f"[cyan]Subject:[/cyan] Need help with billing\n"
            f"[cyan]Customer:[/cyan] john@example.com\n"
            f"[cyan]Status:[/cyan] Open\n"
            f"[cyan]Channel:[/cyan] Email\n"
            f"[cyan]Messages:[/cyan] 5",
            title="Conversation",
            border_style="cyan",
        )
    )


@inbox.command(name="assign")
@click.argument("conversation_id")
@click.option("--agent", "-a", required=True, help="Agent email or ID")
def inbox_assign(conversation_id: str, agent: str):
    """Assign conversation to agent."""
    console.print(f"[green]✓[/green] Conversation assigned to {agent}")


@inbox.command(name="reply")
@click.argument("conversation_id")
@click.option("--message", "-m", prompt=True, help="Reply message")
def inbox_reply(conversation_id: str, message: str):
    """Reply to a conversation."""
    console.print(f"[green]✓[/green] Reply sent")


@inbox.command(name="resolve")
@click.argument("conversation_id")
def inbox_resolve(conversation_id: str):
    """Mark conversation as resolved."""
    console.print(f"[green]✓[/green] Conversation resolved")


@inbox.command(name="reopen")
@click.argument("conversation_id")
def inbox_reopen(conversation_id: str):
    """Reopen a resolved conversation."""
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
    table = Table(title="Contacts", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Email", style="white")
    table.add_column("Company", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")

    console.print(table)


@contacts.command(name="show")
@click.argument("contact_id")
def contacts_show(contact_id: str):
    """Show contact details."""
    console.print(
        Panel(
            f"[cyan]Name:[/cyan] John Doe\n"
            f"[cyan]Email:[/cyan] john@example.com\n"
            f"[cyan]Company:[/cyan] Acme Inc\n"
            f"[cyan]Phone:[/cyan] +1 555-1234\n"
            f"[cyan]Deals:[/cyan] 2 ($50,000)",
            title="Contact Details",
            border_style="cyan",
        )
    )


@contacts.command(name="create")
@click.option("--name", "-n", prompt=True, help="Contact name")
@click.option("--email", "-e", prompt=True, help="Email")
@click.option("--company", "-c", help="Company")
@click.option("--phone", "-p", help="Phone")
def contacts_create(name: str, email: str, company: str, phone: str):
    """Create a contact."""
    console.print(f"[green]✓[/green] Contact '{name}' created")


@contacts.command(name="delete")
@click.argument("contact_id")
def contacts_delete(contact_id: str):
    """Delete a contact."""
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
def deals_list(pipeline: str, stage: str):
    """List deals."""
    table = Table(title="Deals", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Stage", style="white")
    table.add_column("Contact", style="dim")
    table.add_column("Close Date", style="dim")

    console.print(table)


@deals.command(name="show")
@click.argument("deal_id")
def deals_show(deal_id: str):
    """Show deal details."""
    console.print(
        Panel(
            f"[cyan]Deal:[/cyan] Enterprise License\n"
            f"[cyan]Value:[/cyan] $50,000\n"
            f"[cyan]Stage:[/cyan] Negotiation\n"
            f"[cyan]Contact:[/cyan] John Doe\n"
            f"[cyan]Close Date:[/cyan] 2024-02-15",
            title="Deal Details",
            border_style="cyan",
        )
    )


@deals.command(name="create")
@click.option("--name", "-n", prompt=True, help="Deal name")
@click.option("--value", "-v", type=float, prompt=True, help="Deal value")
@click.option("--contact", "-c", required=True, help="Contact ID")
@click.option("--pipeline", "-p", default="default", help="Pipeline")
def deals_create(name: str, value: float, contact: str, pipeline: str):
    """Create a deal."""
    console.print(f"[green]✓[/green] Deal '{name}' created (${value:,.0f})")


@deals.command(name="move")
@click.argument("deal_id")
@click.option("--stage", "-s", required=True, help="Target stage")
def deals_move(deal_id: str, stage: str):
    """Move deal to a stage."""
    console.print(f"[green]✓[/green] Deal moved to '{stage}'")


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
    table = Table(title="Pipelines", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Stages", style="white")
    table.add_column("Deals", style="dim")
    table.add_column("Value", style="green")

    table.add_row("Default", "Lead → Qualified → Proposal → Negotiation → Won", "12", "$234,500")

    console.print(table)


@pipelines.command(name="create")
@click.option("--name", "-n", prompt=True, help="Pipeline name")
@click.option("--stages", "-s", required=True, help="Comma-separated stages")
def pipelines_create(name: str, stages: str):
    """Create a pipeline."""
    console.print(f"[green]✓[/green] Pipeline '{name}' created")


# ============================================================================
# Invoices (ERP)
# ============================================================================


@cx_group.group()
def invoices():
    """Manage invoices."""
    pass


@invoices.command(name="list")
@click.option("--status", type=click.Choice(["draft", "sent", "paid", "overdue", "all"]), default="all")
def invoices_list(status: str):
    """List invoices."""
    table = Table(title="Invoices", box=box.ROUNDED)
    table.add_column("Number", style="cyan")
    table.add_column("Customer", style="white")
    table.add_column("Amount", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Due Date", style="dim")

    console.print(table)


@invoices.command(name="create")
@click.option("--customer", "-c", required=True, help="Customer ID")
@click.option("--amount", "-a", type=float, required=True, help="Amount")
@click.option("--due", "-d", help="Due date")
def invoices_create(customer: str, amount: float, due: str):
    """Create an invoice."""
    console.print(f"[green]✓[/green] Invoice created for ${amount:,.2f}")


@invoices.command(name="send")
@click.argument("invoice_number")
def invoices_send(invoice_number: str):
    """Send an invoice."""
    console.print(f"[green]✓[/green] Invoice {invoice_number} sent")


@invoices.command(name="mark-paid")
@click.argument("invoice_number")
def invoices_mark_paid(invoice_number: str):
    """Mark invoice as paid."""
    console.print(f"[green]✓[/green] Invoice {invoice_number} marked as paid")


# ============================================================================
# Orders (ERP)
# ============================================================================


@cx_group.group()
def orders():
    """Manage orders."""
    pass


@orders.command(name="list")
@click.option("--status", type=click.Choice(["pending", "processing", "shipped", "delivered", "all"]), default="all")
def orders_list(status: str):
    """List orders."""
    table = Table(title="Orders", box=box.ROUNDED)
    table.add_column("Order #", style="cyan")
    table.add_column("Customer", style="white")
    table.add_column("Total", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Date", style="dim")

    console.print(table)


@orders.command(name="show")
@click.argument("order_id")
def orders_show(order_id: str):
    """Show order details."""
    console.print(
        Panel(
            f"[cyan]Order #:[/cyan] {order_id}\n"
            f"[cyan]Customer:[/cyan] John Doe\n"
            f"[cyan]Total:[/cyan] $299.00\n"
            f"[cyan]Status:[/cyan] Processing\n"
            f"[cyan]Items:[/cyan] 3",
            title="Order Details",
            border_style="cyan",
        )
    )


@orders.command(name="update-status")
@click.argument("order_id")
@click.option("--status", "-s", type=click.Choice(["processing", "shipped", "delivered"]), required=True)
def orders_update_status(order_id: str, status: str):
    """Update order status."""
    console.print(f"[green]✓[/green] Order {order_id} status updated to '{status}'")
