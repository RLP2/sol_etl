import requests
import json
from dataclasses import dataclass

url = 'https://api.solanabeach.io/v1/'

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

# API CALL
def _solana_api(limit:int = 1, cursor:int = None):
  '''
  API for fetching latest blocks
  
  Args:
    limit(int) = the number of blocks to retur
    cursor_blocknumber(str) = the starting block number
  
  Return:
    Response(Json) = returned api json
  '''
  api_get = 'latest-blocks'
  
  if not isinstance(limit, int):
    raise TypeError(f'_solana_api: limit requires integer value')
  
  if cursor and not isinstance(cursor, int):
    raise TypeError(f'_solana_api: cursor requires integer value')

  # Set Query Parameters
  query = {'limit': limit}
  if cursor:
    query['cursor'] = str(cursor)
  
  # Call API
  response = requests.get(url + api_get, params=query, auth=BearerAuth(token))
  #print(response)
  if not response.ok:
    raise Error(f"_solana_api api failed: {response}")

  return response.json()

# TRANSFORM
@dataclass
class SolBlock(object):
  '''
  Class for solana block data
  '''
  def __init__(self):
    self.blocknumber: int
    self.blockhash: str
    self.previousblockhash: str
    self.parentslot: int
    self.blocktime_abs: float
    self.blocktime_rel: float
    self.txcount: int
    self.failedtxs: int
    self.totalfees : float
    self.instructions: int
    self.sucessfultxs: int
    self.totalvaluemoved: float
    self.innerinstructions: int

def transform_json(response:json, start_number:float=-float('inf')):
  '''
  Function to parse api response for block data
  
  Args:
    response(json): successful response from api

  Retrun:
    chain(list): list of SolBlocks
  '''

  chain = []
  start_block_number = float('inf')
  end_block_number = -float('inf')
  for record in response:
    block = SolBlock()
    block.blocknumber = record['blocknumber']
    block.blockhash = record['blockhash']
    block.previousblockhash = record['previousblockhash']
    block.parentslot = record['parentslot']
    block.blocktime_abs = record['blocktime']['absolute']
    block.blocktime_rel = record['blocktime']['relative']
    block.txcount = record['metrics']['txcount']
    block.failedtxs = record['metrics']['failedtxs']
    block.totalfees = record['metrics']['totalfees']
    block.instructions = record['metrics']['instructions']
    block.sucessfultxs = record['metrics']['sucessfultxs']
    block.totalvaluemoved = record['metrics']['totalvaluemoved']
    block.innerinstructions = record['metrics']['innerinstructions']
    if block.blocknumber <= start_number:
      break
    chain.append(block)

    start_block_number = min(start_block_number, record['blocknumber'])
    end_block_number = max(end_block_number, record['blocknumber'])
  return chain, start_block_number, end_block_number

# BLOCKS TO APPEND
def create_chain(start_number:int):
  latest_block = _solana_api(limit = 1)
  end_number = latest_block[0]['blocknumber']
  init_end_number = end_number
  chain = []
  while start_number + 1 < end_number:
    
    diff = min(50, end_number - start_number)
    blocks = _solana_api(limit = diff, cursor=end_number)
    rollup, start_roll_number, end_roll_number = transform_json(blocks, start_number)
    chain.extend(rollup)
    end_number = start_roll_number

  return chain, start_number, end_number
