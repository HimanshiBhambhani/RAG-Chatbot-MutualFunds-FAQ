"""
Parser for Groww mutual fund pages.
Extracts structured data from the __NEXT_DATA__ JSON embedded in Next.js pages.
"""

import json
import re
from typing import Optional

from bs4 import BeautifulSoup


def parse_fund_page(html: str, source_url: str) -> dict:
    """
    Parse a Groww mutual fund page and extract structured data from __NEXT_DATA__.

    Groww is a Next.js app that embeds all fund data in a
    <script id="__NEXT_DATA__"> JSON blob under props.pageProps.mfServerSideData.

    Args:
        html: Raw HTML string from the fund page.
        source_url: The URL this page was scraped from.

    Returns:
        Dictionary with extracted fund data fields.
    """
    mf_data = _extract_next_data(html)

    if mf_data is None:
        # Fallback: return minimal data with full text
        return {
            "fund_name": None,
            "nav": None,
            "nav_date": None,
            "aum": None,
            "expense_ratio": None,
            "exit_load": None,
            "min_sip": None,
            "min_lumpsum": None,
            "risk_level": None,
            "category": None,
            "sub_category": None,
            "benchmark": None,
            "fund_managers": [],
            "top_holdings": [],
            "returns": {},
            "description": None,
            "fund_house": None,
            "launch_date": None,
            "rating": None,
            "plan_type": None,
            "scheme_type": None,
            "isin": None,
            "stamp_duty": None,
            "portfolio_turnover": None,
            "lock_in": None,
            "tax_impact": None,
            "sip_allowed": None,
            "lumpsum_allowed": None,
            "source_url": source_url,
            "full_text": extract_full_text(html),
            "_parse_error": "Could not find __NEXT_DATA__ in HTML",
        }

    data = {
        # Basic Info
        "fund_name": mf_data.get("fund_name"),
        "scheme_name": mf_data.get("scheme_name"),
        "description": mf_data.get("description"),
        "fund_house": mf_data.get("fund_house"),
        "amc": mf_data.get("amc"),
        "logo_url": mf_data.get("logo_url"),

        # NAV & Valuation
        "nav": mf_data.get("nav"),
        "nav_date": mf_data.get("nav_date"),
        "aum": mf_data.get("aum"),

        # Costs & Charges
        "expense_ratio": mf_data.get("expense_ratio"),
        "exit_load": mf_data.get("exit_load"),
        "stamp_duty": mf_data.get("stamp_duty"),

        # Investment Limits
        "min_sip": mf_data.get("min_sip_investment"),
        "max_sip": mf_data.get("max_sip_investment"),
        "min_lumpsum": mf_data.get("min_investment_amount"),
        "min_withdrawal": mf_data.get("min_withdrawal"),
        "sip_allowed": mf_data.get("sip_allowed"),
        "lumpsum_allowed": mf_data.get("lumpsum_allowed"),

        # Classification
        "category": mf_data.get("category"),
        "sub_category": mf_data.get("sub_category"),
        "plan_type": mf_data.get("plan_type"),
        "scheme_type": mf_data.get("scheme_type"),
        "risk_level": mf_data.get("nfo_risk"),

        # Performance
        "benchmark": mf_data.get("benchmark"),
        "benchmark_name": mf_data.get("benchmark_name"),
        "portfolio_turnover": mf_data.get("portfolio_turnover"),

        # Identifiers
        "isin": mf_data.get("isin"),
        "scheme_code": mf_data.get("scheme_code"),
        "search_id": mf_data.get("search_id"),

        # Dates
        "launch_date": mf_data.get("launch_date"),
        "allotment_date": mf_data.get("allotment_date"),

        # Rating
        "rating": mf_data.get("groww_rating"),
        "crisil_rating": mf_data.get("crisil_rating"),

        # Lock-in
        "lock_in": _extract_lock_in(mf_data),

        # Fund Managers
        "fund_manager": mf_data.get("fund_manager"),
        "fund_managers": _extract_fund_managers(mf_data),

        # Holdings
        "top_holdings": _extract_holdings(mf_data),
        "holdings_count": len(mf_data.get("holdings", [])),

        # Returns
        "returns": _extract_returns(mf_data),
        "sip_returns": _extract_sip_returns(mf_data),

        # Category Info
        "category_info": _extract_category_info(mf_data),
        "tax_impact": _extract_tax_impact(mf_data),

        # Stats
        "stats": _extract_stats(mf_data),

        # AMC Info
        "amc_info": _extract_amc_info(mf_data),

        # RTA Details
        "rta_details": _extract_rta_details(mf_data),

        # Metadata
        "source_url": source_url,
        "full_text": _build_full_text(mf_data),
    }

    return data


def _extract_next_data(html: str) -> Optional[dict]:
    """Extract mfServerSideData from __NEXT_DATA__ script tag."""
    soup = BeautifulSoup(html, "lxml")
    script = soup.find("script", id="__NEXT_DATA__")

    if not script or not script.string:
        return None

    try:
        next_data = json.loads(script.string)
        return next_data.get("props", {}).get("pageProps", {}).get("mfServerSideData")
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def _extract_lock_in(mf_data: dict) -> Optional[str]:
    """Extract lock-in period as a readable string."""
    lock_in = mf_data.get("lock_in")
    if not lock_in or not isinstance(lock_in, dict):
        return None

    years = lock_in.get("years", 0) or 0
    months = lock_in.get("months", 0) or 0
    days = lock_in.get("days", 0) or 0

    if years == 0 and months == 0 and days == 0:
        return "No lock-in"

    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")

    return ", ".join(parts)


def _extract_fund_managers(mf_data: dict) -> list[dict]:
    """Extract fund manager details."""
    managers_raw = mf_data.get("fund_manager_details", [])
    if not managers_raw:
        return []

    managers = []
    for fm in managers_raw:
        if not isinstance(fm, dict):
            continue
        manager = {
            "name": fm.get("person_name"),
            "education": fm.get("education"),
            "experience": fm.get("experience"),
            "managing_since": fm.get("date_from"),
        }
        # Clean up None values
        manager = {k: v for k, v in manager.items() if v is not None}
        if manager.get("name"):
            managers.append(manager)

    return managers


def _extract_holdings(mf_data: dict) -> list[dict]:
    """Extract top holdings (max 10)."""
    holdings_raw = mf_data.get("holdings", [])
    if not holdings_raw:
        return []

    holdings = []
    for h in holdings_raw[:10]:
        if not isinstance(h, dict):
            continue
        holding = {
            "company_name": h.get("company_name"),
            "sector": h.get("sector_name"),
            "nature": h.get("nature_name"),
            "percentage": h.get("corpus_per"),
            "market_value": h.get("market_value"),
        }
        # Clean up None values
        holding = {k: v for k, v in holding.items() if v is not None}
        if holding.get("company_name"):
            holdings.append(holding)

    return holdings


def _extract_returns(mf_data: dict) -> dict:
    """Extract fund return stats."""
    return_stats = mf_data.get("return_stats", [])
    if not return_stats or not isinstance(return_stats, list):
        return {}

    # First entry is the fund's returns
    fund_returns = return_stats[0] if return_stats else {}
    if not isinstance(fund_returns, dict):
        return {}

    returns = {}
    key_map = {
        "return1d": "1_day",
        "return1w": "1_week",
        "return1m": "1_month",
        "return3m": "3_months",
        "return6m": "6_months",
        "return1y": "1_year",
        "return3y": "3_years",
        "return5y": "5_years",
        "return10y": "10_years",
    }

    for raw_key, label in key_map.items():
        val = fund_returns.get(raw_key)
        if val is not None:
            returns[label] = val

    # Add risk metrics
    for metric in ["sharpe_ratio", "beta", "standard_deviation", "alpha", "r_squared"]:
        val = fund_returns.get(metric)
        if val is not None and val != 0:
            returns[metric] = val

    return returns


def _extract_sip_returns(mf_data: dict) -> dict:
    """Extract SIP return data."""
    sip_return = mf_data.get("sip_return", {})
    if not sip_return or not isinstance(sip_return, dict):
        return {}

    returns = {}
    key_map = {
        "return1y": "1_year",
        "return3y": "3_years",
        "return5y": "5_years",
        "return10y": "10_years",
    }

    for raw_key, label in key_map.items():
        val = sip_return.get(raw_key)
        if val is not None:
            returns[label] = val

    return returns


def _extract_category_info(mf_data: dict) -> Optional[dict]:
    """Extract category details."""
    cat_info = mf_data.get("category_info")
    if not cat_info or not isinstance(cat_info, dict):
        return None

    return {
        "category": cat_info.get("category"),
        "sub_type": cat_info.get("sub_type"),
        "description": cat_info.get("description"),
        "definition": cat_info.get("definition"),
    }


def _extract_tax_impact(mf_data: dict) -> Optional[str]:
    """Extract tax impact info from category_info."""
    cat_info = mf_data.get("category_info")
    if not cat_info or not isinstance(cat_info, dict):
        return None
    return cat_info.get("tax_impact")


def _extract_stats(mf_data: dict) -> list[dict]:
    """Extract performance stats (fund return, category avg, rank)."""
    stats_raw = mf_data.get("stats", [])
    if not stats_raw:
        return []

    stats = []
    for s in stats_raw:
        if not isinstance(s, dict):
            continue
        stat = {
            "type": s.get("type"),
            "title": s.get("title"),
            "1_year": s.get("stat_1y"),
            "3_years": s.get("stat_3y"),
            "5_years": s.get("stat_5y"),
        }
        stat = {k: v for k, v in stat.items() if v is not None}
        if stat.get("type"):
            stats.append(stat)

    return stats


def _extract_amc_info(mf_data: dict) -> Optional[dict]:
    """Extract AMC (fund house) information."""
    amc_info = mf_data.get("amc_info")
    if not amc_info or not isinstance(amc_info, dict):
        return None

    return {
        "name": amc_info.get("name"),
        "aum": amc_info.get("aum"),
        "address": amc_info.get("address"),
        "phone": amc_info.get("phone"),
        "email": amc_info.get("email"),
        "website": amc_info.get("website"),
    }


def _extract_rta_details(mf_data: dict) -> Optional[dict]:
    """Extract registrar & transfer agent details."""
    rta = mf_data.get("rta_details")
    if not rta or not isinstance(rta, dict):
        return None

    return {
        "rta_name": rta.get("rta_name"),
        "custodian_name": rta.get("custodian_name"),
        "email": rta.get("email"),
        "website": rta.get("website"),
    }


def _build_full_text(mf_data: dict) -> str:
    """
    Build a comprehensive text representation of the fund for RAG chunking.
    This is what gets embedded and searched against user queries.
    """
    parts = []

    # Fund identity
    name = mf_data.get("scheme_name") or mf_data.get("fund_name") or "Unknown Fund"
    parts.append(f"Fund Name: {name}")

    fund_house = mf_data.get("fund_house")
    if fund_house:
        parts.append(f"Fund House: {fund_house}")

    desc = mf_data.get("description")
    if desc:
        parts.append(f"Description: {desc}")

    # Classification
    category = mf_data.get("category")
    sub_cat = mf_data.get("sub_category")
    if category:
        cat_str = f"Category: {category}"
        if sub_cat:
            cat_str += f" - {sub_cat}"
        parts.append(cat_str)

    plan_type = mf_data.get("plan_type")
    if plan_type:
        parts.append(f"Plan Type: {plan_type}")

    risk = mf_data.get("nfo_risk")
    if risk:
        parts.append(f"Risk Level: {risk}")

    # NAV & AUM
    nav = mf_data.get("nav")
    nav_date = mf_data.get("nav_date")
    if nav:
        nav_str = f"Current NAV: ₹{nav}"
        if nav_date:
            nav_str += f" (as of {nav_date})"
        parts.append(nav_str)

    aum = mf_data.get("aum")
    if aum:
        parts.append(f"AUM (Fund Size): ₹{aum} Crores")

    # Costs
    expense = mf_data.get("expense_ratio")
    if expense:
        parts.append(f"Expense Ratio: {expense}%")

    exit_load = mf_data.get("exit_load")
    if exit_load:
        parts.append(f"Exit Load: {exit_load}")

    stamp_duty = mf_data.get("stamp_duty")
    if stamp_duty:
        parts.append(f"Stamp Duty: {stamp_duty}")

    # Investment minimums
    min_sip = mf_data.get("min_sip_investment")
    if min_sip:
        parts.append(f"Minimum SIP: ₹{min_sip}")

    min_lump = mf_data.get("min_investment_amount")
    if min_lump:
        parts.append(f"Minimum Lumpsum: ₹{min_lump}")

    sip_allowed = mf_data.get("sip_allowed")
    lump_allowed = mf_data.get("lumpsum_allowed")
    parts.append(f"SIP Allowed: {'Yes' if sip_allowed else 'No'}")
    parts.append(f"Lumpsum Allowed: {'Yes' if lump_allowed else 'No'}")

    # Dates
    launch = mf_data.get("launch_date")
    if launch:
        parts.append(f"Launch Date: {launch}")

    # Benchmark
    benchmark = mf_data.get("benchmark_name") or mf_data.get("benchmark")
    if benchmark:
        parts.append(f"Benchmark: {benchmark}")

    # Fund Managers
    managers = mf_data.get("fund_manager_details", [])
    if managers:
        parts.append("\nFund Managers:")
        for fm in managers:
            if isinstance(fm, dict):
                fm_name = fm.get("person_name", "Unknown")
                fm_exp = fm.get("experience", "")
                parts.append(f"  - {fm_name}")
                if fm_exp:
                    # Truncate long experience text
                    exp_clean = fm_exp.strip().replace("\n", " ")[:200]
                    parts.append(f"    Experience: {exp_clean}")

    # Returns
    return_stats = mf_data.get("return_stats", [])
    if return_stats and isinstance(return_stats[0], dict):
        rs = return_stats[0]
        parts.append("\nReturns (Annualized):")
        return_labels = [
            ("return1m", "1 Month"),
            ("return3m", "3 Months"),
            ("return6m", "6 Months"),
            ("return1y", "1 Year"),
            ("return3y", "3 Years"),
            ("return5y", "5 Years"),
            ("return10y", "10 Years"),
        ]
        for key, label in return_labels:
            val = rs.get(key)
            if val is not None:
                parts.append(f"  {label}: {val}%")

    # Stats comparison
    stats = mf_data.get("stats", [])
    if stats:
        parts.append("\nPerformance Comparison:")
        for s in stats:
            if isinstance(s, dict):
                title = s.get("title", "")
                y1 = s.get("stat_1y")
                y3 = s.get("stat_3y")
                y5 = s.get("stat_5y")
                stat_parts = []
                if y1 is not None:
                    stat_parts.append(f"1Y: {y1}%")
                if y3 is not None:
                    stat_parts.append(f"3Y: {y3}%")
                if y5 is not None:
                    stat_parts.append(f"5Y: {y5}%")
                if stat_parts:
                    parts.append(f"  {title}: {', '.join(stat_parts)}")

    # Top Holdings
    holdings = mf_data.get("holdings", [])
    if holdings:
        parts.append(f"\nTop Holdings ({len(holdings)} total):")
        for h in holdings[:10]:
            if isinstance(h, dict):
                name = h.get("company_name", "Unknown")
                pct = h.get("corpus_per")
                sector = h.get("sector_name", "")
                line = f"  - {name}"
                if pct:
                    line += f" ({pct}%)"
                if sector:
                    line += f" [{sector}]"
                parts.append(line)

    # Category info
    cat_info = mf_data.get("category_info", {})
    if isinstance(cat_info, dict):
        cat_desc = cat_info.get("description")
        if cat_desc:
            parts.append(f"\nCategory Description: {cat_desc}")

        tax = cat_info.get("tax_impact")
        if tax:
            parts.append(f"Tax Impact: {tax}")

    # Lock-in
    lock_in = mf_data.get("lock_in", {})
    if isinstance(lock_in, dict):
        years = lock_in.get("years", 0) or 0
        months = lock_in.get("months", 0) or 0
        days = lock_in.get("days", 0) or 0
        if years or months or days:
            parts.append(f"Lock-in Period: {years}y {months}m {days}d")
        else:
            parts.append("Lock-in Period: None")

    return "\n".join(parts)


def extract_full_text(html: str) -> str:
    """
    Fallback: extract all text from HTML when __NEXT_DATA__ is unavailable.
    Removes navigation, ads, and scripts.

    Args:
        html: Raw HTML string.

    Returns:
        Cleaned text content.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove unwanted elements
    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "iframe"]):
        tag.decompose()

    # Remove common ad/noise elements
    for el in soup.find_all(class_=re.compile(r"ad|banner|popup|cookie|social", re.I)):
        el.decompose()

    # Get text with reasonable spacing
    text = soup.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    return text.strip()
