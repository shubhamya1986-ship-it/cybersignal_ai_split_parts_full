import json
import pandas as pd

def clamp(v):
    return max(0.0,min(100.0,float(v)))

def score_account(r):
    score=0.0
    signals=[]

    ips=float(r.get("unique_ips") or 0)
    ports=float(r.get("unique_ports") or 0)
    products=float(r.get("unique_products") or 0)
    countries=float(r.get("unique_countries") or 0)
    asns=float(r.get("unique_asns") or 0)
    cloud=float(r.get("cloud_observations") or 0)
    iot=float(r.get("iot_observations") or 0)
    sensitive=float(r.get("sensitive_port_observations") or 0)
    http=float(r.get("http_observations") or 0)
    fourxx=float(r.get("http_4xx_observations") or 0)

    # External surface
    if ips >= 10:
        score+=20; signals.append(f"{int(ips)} unique IPs observed")
    elif ips >= 3:
        score+=10; signals.append(f"{int(ips)} unique IPs observed")

    # Service complexity
    if ports >= 8:
        score+=18; signals.append(f"{int(ports)} unique ports observed")
    elif ports >= 4:
        score+=10; signals.append(f"{int(ports)} unique ports observed")

    # Security-relevant services
    if sensitive >= 5:
        score+=20; signals.append(f"{int(sensitive)} observations on security-relevant ports")
    elif sensitive >= 1:
        score+=8; signals.append(f"{int(sensitive)} observation(s) on security-relevant ports")

    # Cloud / IoT
    if cloud>0:
        score+=10; signals.append("Cloud infrastructure observed")
    if iot>0:
        score+=10; signals.append("IoT-related exposure observed")

    # HTTP / technology diversity
    if http>=5:
        score+=7; signals.append("Multiple HTTP services observed")
    if products>=5:
        score+=7; signals.append(f"{int(products)} product/technology types observed")

    # Network/geographic complexity
    if countries>=2 or asns>=3:
        score+=8; signals.append("Infrastructure spans multiple network/geographic contexts")

    # 4xx is only a service-response signal, NOT vulnerability evidence.
    if fourxx>0:
        score+=2; signals.append("HTTP services returned 4xx responses during observation")

    score=round(clamp(score),1)
    priority="High" if score>=65 else "Medium" if score>=35 else "Low"

    last=r.get("last_observed_at")
    why_now=f"Latest observation: {last}" if pd.notna(last) else "Observation recency unavailable"

    return score,priority,json.dumps(signals),why_now
