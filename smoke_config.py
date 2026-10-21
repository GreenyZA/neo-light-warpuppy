from token_optimiser.config import config

t1 = config.tier_backends["T1"]["enabled"]
t2 = len(config.tier_backends["T2"]["gateways"])
t3 = len(config.tier_backends["T3"]["providers"])
print("T1=%s, T2=%d gateways, T3=%d providers" % (t1, t2, t3))
