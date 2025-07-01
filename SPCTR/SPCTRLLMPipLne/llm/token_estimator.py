"""
Token estimation and text batching for LLM context window management
"""
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

class TokenEstimator:
    """Estimate tokens and manage text batching for LLM processing"""
    
    def __init__(self, model_name: str = "llama3.2-3b"):
        # Conservative token limits for different models
        self.model_limits = {
            "llama3.2-3b": 8000,
            "llama3.2-7b": 8000,
            "llama3.2-70b": 8000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 4096
        }
        
        self.max_tokens = self.model_limits.get(model_name, 8000)
        self.safety_margin = 0.8  # Use 80% of available tokens
        
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (conservative estimate)
        Uses ~4 characters per token as a rough approximation
        """
        if not text:
            return 0
        
        # Count characters and estimate tokens
        char_count = len(text)
        
        # Adjust for special characters and formatting
        # Anchor tokens, XML tags, and special formatting use more tokens
        special_chars = len(re.findall(r'<[^>]+>', text))  # XML tags
        anchor_tokens = len(re.findall(r'<A\d{3}>', text))  # Anchor tokens
        
        # Estimate: ~4 chars per token, but special elements use more
        base_tokens = char_count / 4
        special_tokens = (special_chars * 2) + (anchor_tokens * 3)
        
        return int(base_tokens + special_tokens)
    
    def get_available_tokens(self, prompt_tokens: int = 0) -> int:
        """Calculate available tokens for text content"""
        return int(self.max_tokens * self.safety_margin) - prompt_tokens
    
    def split_text_by_anchors(self, text: str, max_tokens: int) -> List[Dict[str, Any]]:
        """
        Split text into batches based on anchor tokens while respecting token limits
        
        Returns:
            List of dictionaries with 'text' and 'batch_info'
        """
        if not text:
            return []
        
        # Find all anchor tokens and their positions
        anchor_pattern = r'<A\d{3}>'
        anchors = list(re.finditer(anchor_pattern, text))
        
        if not anchors:
            # No anchors found, split by paragraphs
            return self.split_text_by_paragraphs(text, max_tokens)
        
        batches = []
        current_batch = ""
        current_anchors = []
        batch_start_anchor = None
        
        for i, anchor_match in enumerate(anchors):
            anchor_token = anchor_match.group()
            anchor_start = anchor_match.start()
            
            # Get text from previous anchor to current anchor
            if i == 0:
                # First anchor - include text from start
                segment_text = text[:anchor_start] + anchor_token
            else:
                # Get text from previous anchor to current anchor
                prev_end = anchors[i-1].end()
                segment_text = text[prev_end:anchor_start] + anchor_token
            
            # Check if adding this segment would exceed token limit
            test_batch = current_batch + segment_text
            estimated_tokens = self.estimate_tokens(test_batch)
            
            if estimated_tokens > max_tokens and current_batch:
                # Current batch is full, save it and start new one
                batch_info = {
                    'start_anchor': batch_start_anchor,
                    'end_anchor': current_anchors[-1] if current_anchors else None,
                    'anchor_count': len(current_anchors),
                    'estimated_tokens': self.estimate_tokens(current_batch)
                }
                
                batches.append({
                    'text': current_batch,
                    'batch_info': batch_info
                })
                
                # Start new batch with current segment
                current_batch = segment_text
                current_anchors = [anchor_token]
                batch_start_anchor = anchor_token
            else:
                # Add to current batch
                current_batch = test_batch
                current_anchors.append(anchor_token)
                if not batch_start_anchor:
                    batch_start_anchor = anchor_token
        
        # Add final batch
        if current_batch:
            batch_info = {
                'start_anchor': batch_start_anchor,
                'end_anchor': current_anchors[-1] if current_anchors else None,
                'anchor_count': len(current_anchors),
                'estimated_tokens': self.estimate_tokens(current_batch)
            }
            
            batches.append({
                'text': current_batch,
                'batch_info': batch_info
            })
        
        return batches
    
    def split_text_by_paragraphs(self, text: str, max_tokens: int) -> List[Dict[str, str]]:
        """Fallback: split text by paragraphs when no anchors are found"""
        paragraphs = text.split('\n\n')
        batches = []
        current_batch = ""
        
        for paragraph in paragraphs:
            test_batch = current_batch + paragraph + '\n\n'
            estimated_tokens = self.estimate_tokens(test_batch)
            
            if estimated_tokens > max_tokens and current_batch:
                batches.append({
                    'text': current_batch.strip(),
                    'batch_info': {
                        'start_anchor': None,
                        'end_anchor': None,
                        'anchor_count': 0,
                        'estimated_tokens': self.estimate_tokens(current_batch)
                    }
                })
                current_batch = paragraph + '\n\n'
            else:
                current_batch = test_batch
        
        if current_batch:
            batches.append({
                'text': current_batch.strip(),
                'batch_info': {
                    'start_anchor': None,
                    'end_anchor': None,
                    'anchor_count': 0,
                    'estimated_tokens': self.estimate_tokens(current_batch)
                }
            })
        
        return batches
    
    def analyze_text_size(self, text: str, prompt_text: str = "") -> Dict[str, Any]:
        """
        Analyze text size and provide batching recommendations
        
        Returns:
            Dictionary with analysis results and recommendations
        """
        text_tokens = self.estimate_tokens(text)
        prompt_tokens = self.estimate_tokens(prompt_text)
        total_tokens = text_tokens + prompt_tokens
        available_tokens = self.get_available_tokens(prompt_tokens)
        
        analysis = {
            'text_tokens': text_tokens,
            'prompt_tokens': prompt_tokens,
            'total_tokens': total_tokens,
            'available_tokens': available_tokens,
            'max_tokens': self.max_tokens,
            'fits_in_context': total_tokens <= available_tokens,
            'needs_batching': total_tokens > available_tokens,
            'utilization_percent': (total_tokens / self.max_tokens) * 100
        }
        
        if analysis['needs_batching']:
            batches = self.split_text_by_anchors(text, available_tokens)
            analysis['recommended_batches'] = len(batches)
            analysis['batch_details'] = [
                {
                    'batch_num': i + 1,
                    'estimated_tokens': batch['batch_info']['estimated_tokens'],
                    'anchor_count': batch['batch_info']['anchor_count'],
                    'start_anchor': batch['batch_info']['start_anchor'],
                    'end_anchor': batch['batch_info']['end_anchor']
                }
                for i, batch in enumerate(batches)
            ]
        
        return analysis
    
    def get_debug_info(self, text: str, prompt_text: str = "") -> str:
        """Get formatted debug information for token analysis"""
        analysis = self.analyze_text_size(text, prompt_text)
        
        debug_info = f"""
🔍 TOKEN ANALYSIS DEBUG INFO
{'='*50}
📊 Token Counts:
   • Text tokens: {analysis['text_tokens']:,}
   • Prompt tokens: {analysis['prompt_tokens']:,}
   • Total tokens: {analysis['total_tokens']:,}
   • Available tokens: {analysis['available_tokens']:,}
   • Max model tokens: {analysis['max_tokens']:,}

📈 Utilization:
   • Context utilization: {analysis['utilization_percent']:.1f}%
   • Fits in context: {'✅ YES' if analysis['fits_in_context'] else '❌ NO'}
   • Needs batching: {'✅ YES' if analysis['needs_batching'] else '❌ NO'}

"""
        
        if analysis['needs_batching']:
            debug_info += f"📦 Batching Required:\n"
            debug_info += f"   • Recommended batches: {analysis['recommended_batches']}\n"
            debug_info += f"   • Batch details:\n"
            
            for batch in analysis['batch_details']:
                debug_info += f"     - Batch {batch['batch_num']}: {batch['estimated_tokens']:,} tokens"
                if batch['start_anchor']:
                    debug_info += f" ({batch['start_anchor']} to {batch['end_anchor']})"
                debug_info += f" ({batch['anchor_count']} anchors)\n"
        
        return debug_info 