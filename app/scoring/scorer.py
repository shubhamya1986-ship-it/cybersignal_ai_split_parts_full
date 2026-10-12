import json

def account_context(row):
    def g(k,d=None):
        v=row.get(k,d)
        return d if v is None else v

    try:
        signals=json.loads(g("signals","[]"))
    except Exception:
        signals=[]

    return {
        "org":g("org","Unknown"),
        "score":float(g("score",0)),
        "priority":g("priority","Low"),
        "signals":signals,
        "why_now":g("why_now",""),
        "unique_ips":int(g("unique_ips",0)),
        "unique_ports":int(g("unique_ports",0)),
        "unique_products":int(g("unique_products",0)),
        "unique_countries":int(g("unique_countries",0)),
        "unique_asns":int(g("unique_asns",0)),
        "cloud_observations":int(g("cloud_observations",0)),
        "iot_observations":int(g("iot_observations",0)),
        "http_observations":int(g("http_observations",0)),
        "sensitive_port_observations":int(g("sensitive_port_observations",0)),
        "last_observed_at":str(g("last_observed_at",""))
    }
