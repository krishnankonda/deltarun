from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_analysis_response(response: Dict[str, Any], job_name: str) -> None:
    """Format and display the analysis response in a human-readable format"""
    
    console.print(f"\n[bold cyan]Analyzing cost profile for '{job_name}'...[/bold cyan]\n")
    
    # Extract data from response
    data_local = response.get("data_local_option", {})
    remote_options = response.get("remote_options", [])
    
    # Display data-local option
    console.print("[bold]Based on your data location, the \"Data-Local\" option is:[/bold]")
    console.print(f"  Provider: {data_local.get('provider', 'N/A')} ({data_local.get('region', 'N/A')})")
    console.print(f"  Est. Compute Cost: ${data_local.get('compute_cost_per_hour', 0):.2f}/hr\n")
    
    # Display remote options
    if remote_options:
        console.print("[bold][Remote Options][/bold]\n")
        
        for option in remote_options:
            provider = option.get("provider", "N/A")
            region = option.get("region", "N/A")
            instance_type = option.get("instance_type", "")
            compute_cost = option.get("compute_cost_per_hour", 0)
            egress_cost = option.get("one_time_egress_cost", 0)
            break_even = option.get("break_even_hours")
            advisory = option.get("advisory_message", "")
            is_spot = option.get("is_spot_instance", False)
            interruption_risk = option.get("interruption_risk")
            
            # Build provider/region string
            provider_str = f"{provider} ({region})"
            if is_spot:
                provider_str += " [yellow](SPOT INSTANCE)[/yellow]"
            
            console.print(f"  Provider: {provider_str}")
            
            # Instance type
            if instance_type:
                console.print(f"  Instance Type: {instance_type}")
            
            # Compute cost
            cost_str = f"${compute_cost:.2f}/hr"
            if is_spot:
                cost_str += " [yellow](Volatile)[/yellow]"
            console.print(f"  Est. Compute Cost: {cost_str}")
            
            # Interruption risk for spot instances
            if is_spot and interruption_risk:
                risk_color = {
                    "LOW": "green",
                    "MEDIUM": "yellow",
                    "HIGH": "red"
                }.get(interruption_risk, "white")
                console.print(f"  Interruption Risk: [{risk_color}]{interruption_risk}[/{risk_color}]")
            
            # Egress cost
            if egress_cost > 0:
                console.print(f"  One-Time Egress: ${egress_cost:,.2f}")
            
            # Break-even
            if break_even is not None:
                console.print(f"  BREAK-EVEN: {break_even:.1f} hours")
            
            # Advisory
            console.print(f"  > ADVISORY: {advisory}\n")
    else:
        console.print("[yellow]No remote options available.[/yellow]\n")


def format_error(error: str) -> None:
    """Format and display an error message"""
    console.print(f"[bold red]Error:[/bold red] {error}")

