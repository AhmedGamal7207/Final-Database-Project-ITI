import asyncio
import httpx
import logging
import time
from typing import List, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class Role(Enum):
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"

class ReplicationManager:
    def __init__(self, node_id: int, peers: List[str], db_engine):
        self.node_id = node_id
        self.peers = peers # List of "http://host:port"
        self.role = Role.FOLLOWER
        self.leader: Optional[str] = None
        self.term = 0
        self.last_heartbeat = time.time()
        self.db = db_engine
        
        self.election_timeout_min = 1.5
        self.election_timeout_max = 3.0
        self.heartbeat_interval = 0.5
        self.client = httpx.AsyncClient(timeout=1.0)
        self._loop_task = None
        self._reset_election_deadline()
    
    def _reset_election_deadline(self):
        import random
        delay = random.uniform(self.election_timeout_min, self.election_timeout_max)
        self.election_deadline = time.time() + delay

    async def start(self):
        # Start background tasks
        self._loop_task = asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        while True:
            if self.role == Role.LEADER:
                await self._send_heartbeats()
            else:
                await self._check_election_timeout()
            
            await asyncio.sleep(0.1)

    async def _send_heartbeats(self):
        for peer in self.peers:
            try:
                # Fire and forget / Log errors
                await self.client.post(f"{peer}/internal/heartbeat", json={"term": self.term, "leader_id": self.node_id})
            except Exception as e:
                pass
        await asyncio.sleep(self.heartbeat_interval)

    async def _check_election_timeout(self):
        if time.time() > self.election_deadline:
            logger.info("Election timeout! becoming candidate.")
            await self._start_election()
            self._reset_election_deadline()

    async def _start_election(self):
        self.role = Role.CANDIDATE
        self.term += 1
        self.vote_count = 1 # Self
        # Simplified: Request votes
        # In this simple logic, highest ID wins or first to request wins?
        # Let's simple ask everyone.
        
        for peer in self.peers:
            try:
                resp = await self.client.post(f"{peer}/internal/vote", json={"term": self.term, "candidate_id": self.node_id})
                if resp.status_code == 200 and resp.json().get("vote_granted"):
                    self.vote_count += 1
            except:
                pass
        
        if self.vote_count > (len(self.peers) + 1) // 2:
            self.role = Role.LEADER
            self.leader = self.node_id
            logger.info(f"Won election. I am LEADER {self.node_id}")
            # Announce
            await self._send_heartbeats()
        else:
            # Random backoff
            await asyncio.sleep(0.5)

    def receive_heartbeat(self, term: int, leader_id: int):
        self.last_heartbeat = time.time()
        self._reset_election_deadline()
        if term >= self.term:
            self.term = term
            self.role = Role.FOLLOWER
            self.leader = leader_id

    def receive_vote_request(self, term: int, candidate_id: int) -> bool:
        if term > self.term:
            self.term = term
            self.role = Role.FOLLOWER
            self._reset_election_deadline()
            return True
        return False

    async def replicate_to_peers(self, op_data: dict):
        # Called by Primary after local write
        if self.role != Role.LEADER:
            return
        
        # Best effort or Quorum? Requirement: "Replicate..."
        # We will try to send to all.
        for peer in self.peers:
            try:
                resp = await self.client.post(f"{peer}/internal/replicate", json=op_data)
                if resp.status_code != 200:
                    logger.error(f"Replication failed to {peer}: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"Replication connection error to {peer}: {e}")

