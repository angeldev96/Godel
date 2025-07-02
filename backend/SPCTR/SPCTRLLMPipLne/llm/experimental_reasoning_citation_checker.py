"""
Experimental Reasoning-Based Citation Checker
Bypasses base citation extraction and sends anchored text directly to reasoning model
"""
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum

# Add parent directory to path to import from core and config folders
sys.path.append(str(Path(__file__).parent.parent))

from config.config import config, LLMProvider
from llm.llm_client import LLMClient, LLMClientFactory
from llm.token_estimator import TokenEstimator
from utils.metadata_manager import MetadataManager

class ReasoningEffort(Enum):
    """Reasoning effort levels for OpenAI reasoning models"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ExperimentalReasoningCitationChecker:
    """Experimental citation checker that uses reasoning models directly"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-2024-08-06"):
        self.api_key = api_key or config.get_api_key(LLMProvider.OPENAI)
        self.model = model
        self.client = None
        self.token_estimator = TokenEstimator()
        self.working_dir = Path.cwd()
        self.metadata_manager = MetadataManager(self.working_dir)
        self.default_effort = ReasoningEffort.HIGH
        
        if not self.api_key:
            print("❌ OpenAI API key required for reasoning models")
            return
        
        # Initialize OpenAI client for reasoning models
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            print(f"✅ Experimental reasoning checker initialized with model: {model}")
        except ImportError:
            print("❌ OpenAI SDK not installed. Please install with: pip install openai")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
    
    def check_citations_direct(
        self, 
        anchored_text: str, 
        output_file: Optional[str] = None,
        effort: ReasoningEffort = ReasoningEffort.HIGH,
        debug: bool = False,
        batch_size: int = 10,
        context_overlap: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Check citations directly using reasoning model without base extraction
        
        Args:
            anchored_text: Text with anchor tokens
            output_file: Optional output file path
            effort: Reasoning effort level
            debug: Enable debug output
            batch_size: Number of citations to process per batch
            context_overlap: Number of overlapping citations between batches
            
        Returns:
            Dictionary with citation analysis results
        """
        if not self.client:
            print("❌ No OpenAI client available")
            return None
        
        # Create metadata for this processing operation
        metadata = self.metadata_manager.create_document_metadata("experimental_reasoning_check")
        processing_id = metadata["processing_id"]
        
        print(f"🧠 EXPERIMENTAL MODE: Direct reasoning-based citation checking")
        print(f"🆔 Processing ID: {processing_id}")
        print(f"⏰ Start Time: {metadata['processing']['start_time']}")
        
        # Load the legal citation prompt
        prompt_template = self._load_legal_citation_prompt()
        if not prompt_template:
            print("❌ Failed to load legal citation prompt")
            return None
        
        # Analyze token usage
        if debug:
            self._analyze_token_usage(anchored_text, prompt_template)
        
        # Check if batching is needed
        text_tokens = self.token_estimator.estimate_tokens(anchored_text)
        prompt_tokens = self.token_estimator.estimate_tokens(prompt_template)
        total_tokens = text_tokens + prompt_tokens
        max_tokens = 100000  # Much higher limit for gpt-4o-2024-08-06 (128K context)
        
        if total_tokens > max_tokens:
            print(f"📦 Text requires batching (total tokens: {total_tokens:,})")
            return self._process_batched_direct_check(
                anchored_text, prompt_template, output_file, effort, debug, 
                batch_size, context_overlap, metadata
            )
        else:
            print(f"📄 Processing single batch (total tokens: {total_tokens:,})")
            return self._process_single_batch_direct_check(
                anchored_text, prompt_template, output_file, effort, debug, metadata
            )
    
    def _load_legal_citation_prompt(self) -> Optional[str]:
        """Load the legal citation prompt template"""
        # Use a much shorter, focused prompt for experimental reasoning
        short_prompt = """You are a legal citation expert. Analyze the provided text for legal citations and return them in JSON format.

CITATION TYPES TO FIND:
- Case citations (e.g., "Smith v. Jones, 123 U.S. 456 (2020)")
- Statutory citations (e.g., "42 U.S.C. § 1983")
- Regulatory citations (e.g., "28 C.F.R. § 35.104")
- Constitutional citations (e.g., "U.S. Const. art. I, § 8")
- Court rules (e.g., "Fed. R. Civ. P. 12(b)(6)")

OUTPUT FORMAT:
Return a JSON array with each citation found:
```json
[
  {
    "anchor": "P-00042",
    "start_offset": 12,
    "end_offset": 31,
    "type": "case",
    "status": "Correct",
    "errors": [],
    "orig": "Roe v. Wade, 410 U.S. 113 (1973)",
    "suggested": "Roe v. Wade, 410 U.S. 113 (1973)"
  }
]
```

RULES:
- Examine each paragraph (marked by ⟦P-#####⟧ anchors)
- Look for any legal citations in the text
- If no citations found, return []
- Be thorough but only include actual legal citations"""
        
        return short_prompt
    
    def _analyze_token_usage(self, text: str, prompt: str):
        """Analyze and display token usage information"""
        text_tokens = self.token_estimator.estimate_tokens(text)
        prompt_tokens = self.token_estimator.estimate_tokens(prompt)
        total_tokens = text_tokens + prompt_tokens
        max_tokens = 100000  # Much higher limit for gpt-4o-2024-08-06
        
        print("\n🔍 TOKEN ANALYSIS DEBUG INFO")
        print("=" * 50)
        print(f"📊 Token Counts:")
        print(f"   • Text tokens: {text_tokens:,}")
        print(f"   • Prompt tokens: {prompt_tokens:,}")
        print(f"   • Total tokens: {total_tokens:,}")
        print(f"   • Available tokens: {max_tokens - total_tokens:,}")
        print(f"   • Max model tokens: {max_tokens:,}")
        print()
        print(f"📈 Utilization:")
        print(f"   • Context utilization: {(total_tokens / max_tokens) * 100:.1f}%")
        print(f"   • Fits in context: {'✅ YES' if total_tokens <= max_tokens else '❌ NO'}")
        print(f"   • Needs batching: {'✅ YES' if total_tokens > max_tokens else '❌ NO'}")
        print()
    
    def _process_single_batch_direct_check(
        self, 
        anchored_text: str, 
        prompt_template: str,
        output_file: Optional[str],
        effort: ReasoningEffort,
        debug: bool,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process a single batch of text directly with reasoning model"""
        
        if not self.client:
            print("❌ No OpenAI client available for reasoning model")
            return None
        
        # Create the full prompt
        full_prompt = f"{prompt_template}\n\n## DOCUMENT TEXT TO ANALYZE\n\n{anchored_text}"
        
        if debug:
            print(f"📤 Sending {len(anchored_text):,} characters to reasoning model...")
        
        try:
            # Call OpenAI API (regular chat completion, not reasoning API)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                max_tokens=16000,  # Higher output limit for gpt-4o-2024-08-06
                temperature=0.1  # Low temperature for consistent results
            )
            
            if not response.choices or not response.choices[0].message.content:
                print("❌ No output from model")
                return None
            
            response_text = response.choices[0].message.content
            
            # Save raw output
            raw_output_file = self.metadata_manager.create_output_filename(
                "experimental_reasoning", metadata["processing_id"], "raw", ".txt"
            )
            with open(raw_output_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            
            if debug:
                print(f"💾 Raw reasoning output saved to: {raw_output_file}")
                print(f"📄 Full response length: {len(response_text):,} characters")
                print(f"📄 Response preview: {response_text[:200]}...")
                print(f"📄 Response ending: ...{response_text[-200:]}")
            
            # Parse the response
            citations = self._parse_reasoning_response(response_text, debug)
            
            if citations is None:
                print("❌ Failed to parse reasoning response")
                return None
            
            # Create results
            results = {
                "citations": citations,
                "total_citations": len(citations),
                "errors": sum(1 for c in citations if c.get('status') == 'Error'),
                "correct": sum(1 for c in citations if c.get('status') == 'Correct'),
                "uncertain": sum(1 for c in citations if c.get('status') == 'Uncertain'),
                "processing_mode": "experimental_reasoning_direct",
                "model_used": self.model,
                "reasoning_effort": effort.value,
                "metadata": metadata
            }
            
            # Save results
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"💾 Results saved to: {output_file}")
            
            # Update metadata
            metadata = self.metadata_manager.add_pipeline_step(
                metadata, "experimental_reasoning_check", 
                "anchored_text", output_file, "completed"
            )
            self.metadata_manager.save_metadata(metadata)
            
            return results
            
        except Exception as e:
            print(f"❌ Reasoning API call failed: {e}")
            return None
    
    def _process_batched_direct_check(
        self, 
        anchored_text: str, 
        prompt_template: str,
        output_file: Optional[str],
        effort: ReasoningEffort,
        debug: bool,
        batch_size: int,
        context_overlap: int,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process text in batches using reasoning model"""
        
        # Split text into paragraphs
        paragraphs = self._split_into_paragraphs(anchored_text)
        
        if debug:
            print(f"📦 Text split into {len(paragraphs)} paragraphs")
            print(f"📦 Processing in batches of {batch_size} paragraphs")
        
        all_citations = []
        batch_count = (len(paragraphs) + batch_size - 1) // batch_size
        
        for batch_num in range(batch_count):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(paragraphs))
            
            # Get batch paragraphs
            batch_paragraphs = paragraphs[start_idx:end_idx]
            batch_text = "\n\n".join(batch_paragraphs)
            
            if debug:
                print(f"📦 Processing batch {batch_num + 1}/{batch_count} ({len(batch_paragraphs)} paragraphs)")
            
            # Process this batch
            batch_results = self._process_single_batch_direct_check(
                batch_text, prompt_template, None, effort, debug, metadata
            )
            
            if batch_results and batch_results.get('citations'):
                all_citations.extend(batch_results['citations'])
        
        # Combine results
        if all_citations:
            results = {
                "citations": all_citations,
                "total_citations": len(all_citations),
                "errors": sum(1 for c in all_citations if c.get('status') == 'Error'),
                "correct": sum(1 for c in all_citations if c.get('status') == 'Correct'),
                "uncertain": sum(1 for c in all_citations if c.get('status') == 'Uncertain'),
                "processing_mode": "experimental_reasoning_batched",
                "model_used": self.model,
                "reasoning_effort": effort.value,
                "batches_processed": batch_count,
                "metadata": metadata
            }
            
            # Save results
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"💾 Results saved to: {output_file}")
            
            return results
        else:
            print("❌ No citations found in any batch")
            return None
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split anchored text into paragraphs"""
        # Split by double newlines to get paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return paragraphs
    
    def _parse_reasoning_response(self, response_text: str, debug: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Parse the reasoning model response to extract citations"""
        try:
            # First try to find JSON array in markdown code blocks
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON array without markdown - be more specific
                # Look for array that starts with [ and ends with ] and contains citation objects
                json_match = re.search(r'\[\s*\{[^[]*\}\s*(?:,\s*\{[^[]*\}\s*)*\]', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    # Last resort: try to find any array that might be JSON
                    json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        if debug:
                            print("❌ No JSON array found in response")
                        return None
            
            # Parse JSON
            citations = json.loads(json_str)
            
            if debug:
                print(f"✅ Successfully parsed {len(citations)} citations from reasoning response")
            
            return citations
            
        except json.JSONDecodeError as e:
            if debug:
                print(f"❌ JSON parsing error: {e}")
                print(f"📄 Raw JSON string: {json_str[:200]}...")
            return None
        except Exception as e:
            if debug:
                print(f"❌ Response parsing error: {e}")
            return None

def main():
    """CLI interface for experimental reasoning citation checker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Experimental Reasoning-Based Citation Checker")
    parser.add_argument("input_file", help="Path to anchored text file")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--effort", choices=["low", "medium", "high"], default="high",
                       help="Reasoning effort level (default: high)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    
    args = parser.parse_args()
    
    # Read input file
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            anchored_text = f.read()
    except Exception as e:
        print(f"❌ Failed to read input file: {e}")
        return
    
    # Initialize checker
    checker = ExperimentalReasoningCitationChecker()
    
    # Check citations
    results = checker.check_citations_direct(
        anchored_text=anchored_text,
        output_file=args.output,
        effort=ReasoningEffort(args.effort) if args.effort else ReasoningEffort.HIGH,
        debug=args.debug,
        batch_size=args.batch_size
    )
    
    if results:
        print(f"\n📊 EXPERIMENTAL REASONING RESULTS:")
        print(f"   • Total citations: {results['total_citations']}")
        print(f"   • Correct: {results['correct']}")
        print(f"   • Errors: {results['errors']}")
        print(f"   • Uncertain: {results['uncertain']}")
        print(f"   • Processing mode: {results['processing_mode']}")
        print(f"   • Model used: {results['model_used']}")
        print(f"   • Reasoning effort: {results['reasoning_effort']}")
    else:
        print("❌ Citation checking failed")

if __name__ == "__main__":
    main() 