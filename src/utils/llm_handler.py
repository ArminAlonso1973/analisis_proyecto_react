from typing import List, Dict, Any, Optional
import asyncio
import hashlib
import json
from pathlib import Path
import openai
from ..core.config import LLMConfig

class LLMHandler:
    def __init__(self, config: LLMConfig, cache_dir: Path):
        self.config = config
        self.cache_dir = cache_dir
        self.semaphore = asyncio.Semaphore(config.batch_size)
        
    def _get_cache_key(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None
    
    def _cache_response(self, cache_key: str, response: Dict):
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_file.write_text(json.dumps(response))
    
    async def analyze_chunk(self, chunk: str, context: str = "") -> Dict:
        prompt = self._create_prompt(chunk, context)
        cache_key = self._get_cache_key(prompt)
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        async with self.semaphore:
            try:
                response = await openai.ChatCompletion.acreate(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": self.config.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                result = json.loads(response.choices[0].message.content)
                self._cache_response(cache_key, result)
                return result
            except Exception as e:
                print(f"Error in LLM analysis: {e}")
                return {}

    def _create_prompt(self, chunk: str, context: str) -> str:
        return f"""Analyze the following code in the context of {context}.
        Extract and provide a JSON response with:
        1. Entities...
        2. Processes...
        ...
        Code to analyze:
        {chunk}
        Provide the response in the following JSON format:
        ...
        """
