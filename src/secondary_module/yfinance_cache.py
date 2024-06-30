import os
import yaml
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter


# Assuming yfinance_cache_and_limit.py is in src/secondary_module/yfinance_cache_and_limit.py
project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
config_path = os.path.join(project_root_path, 'conf', 'config.yaml')
with open(config_path, 'r') as yaml_conf:
    config = yaml.safe_load(yaml_conf)
    
    
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

session = CachedLimiterSession(
    # max X requests per Y seconds
    limiter=Limiter(RequestRate(config['yfinance_API_REQUESTS_RATE_NUMBER'], Duration.SECOND * config['yfinance_API_REQUESTS_RATE_SECONDS'])),  
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache"),
)