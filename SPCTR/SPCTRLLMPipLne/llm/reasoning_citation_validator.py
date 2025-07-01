"""
Reasoning-based Citation Validator - Second-pass analysis using OpenAI reasoning models
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

class ReasoningEffort(Enum):
    """Reasoning effort levels for OpenAI reasoning models"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ReasoningCitationValidator:
    """Second-pass citation validator using OpenAI reasoning models"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "o4-mini"):
        self.api_key = api_key or config.get_api_key(LLMProvider.OPENAI)
        self.model = model
        self.client = None
        
        if not self.api_key:
            print("❌ OpenAI API key required for reasoning models")
            return
        
        # Initialize OpenAI client for reasoning models
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            print(f"✅ Reasoning validator initialized with model: {model}")
        except ImportError:
            print("❌ OpenAI SDK not installed. Please install with: pip install openai")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
    
    def validate_citations_with_reasoning(
        self, 
        citations: List[Dict[str, Any]], 
        original_text: str,
        effort: ReasoningEffort = ReasoningEffort.MEDIUM,
        debug: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Validate citations using OpenAI reasoning models for deeper analysis
        
        Args:
            citations: List of citations from first-pass analysis
            original_text: Original text containing the citations
            effort: Reasoning effort level (low, medium, high)
            debug: Enable debug output
            
        Returns:
            List of validated citations with improved accuracy
        """
        if not self.client:
            print("❌ No OpenAI client available")
            return citations
        
        if not citations:
            return []
        
        print(f"🧠 Validating {len(citations)} citations with reasoning model...")
        
        validated_citations = []
        
        for i, citation in enumerate(citations):
            if debug:
                print(f"   📝 Validating citation {i+1}/{len(citations)}: {citation.get('orig', 'Unknown')}")
            
            # Determine if this citation needs reasoning validation
            needs_reasoning = self._needs_reasoning_validation(citation)
            
            if needs_reasoning:
                validated_citation = self._validate_single_citation_with_reasoning(
                    citation, original_text, effort, debug
                )
                if validated_citation:
                    validated_citations.append(validated_citation)
                else:
                    # Fallback to original citation if reasoning fails
                    validated_citations.append(citation)
            else:
                # Citation is clear, no reasoning needed
                validated_citations.append(citation)
        
        print(f"✅ Reasoning validation complete: {len(validated_citations)} citations processed")
        return validated_citations
    
    def _needs_reasoning_validation(self, citation: Dict[str, Any]) -> bool:
        """
        Determine if a citation needs reasoning-based validation
        
        Returns:
            True if the citation needs deeper analysis
        """
        status = citation.get('status', '')
        errors = citation.get('errors', [])
        orig = citation.get('orig', '')
        suggested = citation.get('suggested', '')
        
        # Cases that need reasoning:
        
        # 1. Uncertain status
        if status == 'Uncertain':
            return True
        
        # 2. Error status but no specific errors listed
        if status == 'Error' and not errors:
            return True
        
        # 3. Error status but suggested correction is identical to original
        if status == 'Error' and orig == suggested:
            return True
        
        # 4. Complex citations that might be false positives
        complex_patterns = [
            r'\d+ U\.S\.C\.',  # Federal statutes
            r'\d+ C\.F\.R\.',  # Federal regulations
            r'U\.S\. Const\.',  # Constitutional citations
            r'\d+ F\.\d+',      # Federal cases
            r'\d+ S\.Ct\.',     # Supreme Court cases
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, orig):
                return True
        
        # 5. Citations with multiple potential interpretations
        if len(orig.split()) > 8:  # Long citations
            return True
        
        return False
    
    def _validate_single_citation_with_reasoning(
        self, 
        citation: Dict[str, Any], 
        original_text: str,
        effort: ReasoningEffort,
        debug: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Validate a single citation using reasoning model
        """
        if not self.client:
            print(f"      ❌ No OpenAI client available")
            return citation
            
        try:
            # Create reasoning prompt
            prompt = self._create_reasoning_prompt(citation, original_text)
            
            if debug:
                print(f"      🤔 Sending to reasoning model with {effort.value} effort...")
            
            # Call OpenAI reasoning API
            response = self.client.responses.create(
                model=self.model,
                reasoning={"effort": effort.value},
                input=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_output_tokens=4000  # Reserve space for reasoning
            )
            
            if response.status == "incomplete":
                print(f"      ⚠️  Reasoning incomplete - ran out of tokens")
                return citation
            
            if not response.output_text:
                print(f"      ❌ No output from reasoning model")
                return citation
            
            # Parse reasoning response
            validated_citation = self._parse_reasoning_response(
                response.output_text, citation, debug
            )
            
            if validated_citation:
                if debug:
                    print(f"      ✅ Reasoning validation successful")
                return validated_citation
            else:
                print(f"      ❌ Failed to parse reasoning response")
                return citation
                
        except Exception as e:
            print(f"      ❌ Reasoning validation failed: {e}")
            return citation
    
    def _create_reasoning_prompt(self, citation: Dict[str, Any], original_text: str) -> str:
        """
        Create a comprehensive reasoning prompt for citation validation
        """
        anchor = citation.get('anchor', '')
        citation_type = citation.get('type', '')
        status = citation.get('status', '')
        errors = citation.get('errors', [])
        orig = citation.get('orig', '')
        suggested = citation.get('suggested', '')
        
        # Extract context around the citation
        context = self._extract_citation_context(original_text, anchor, orig)
        
        prompt = f"""
You are a legal citation expert with deep knowledge of Bluebook citation rules. You need to perform a thorough analysis of a legal citation that was flagged for deeper review.

## CITATION TO ANALYZE:
- **Original Citation**: "{orig}"
- **Current Status**: {status}
- **Citation Type**: {citation_type}
- **Current Errors**: {errors}
- **Current Suggestion**: "{suggested}"

## CONTEXT:
The citation appears in this context:
{context}

## YOUR TASK:
Perform a comprehensive analysis of this citation considering:

1. **Citation Identification**: Is this actually a legal citation that should be analyzed?
2. **Citation Type**: What type of legal authority is this (case, statute, regulation, etc.)?
3. **Bluebook Compliance**: Does it follow proper Bluebook formatting rules?
4. **Error Detection**: Are there any formatting, punctuation, or structural errors?
5. **Correction Accuracy**: If errors exist, what is the correct Bluebook format?

## ANALYSIS REQUIREMENTS:
- Think step-by-step through the Bluebook rules that apply
- Consider the citation's context and purpose
- Verify any legal references (case names, statutes, etc.)
- Check for common Bluebook violations
- Determine if this is a false positive (not actually a citation)

## OUTPUT FORMAT:
Return your analysis in this exact JSON format:

```json
{{
  "anchor": "{anchor}",
  "start_offset": <number>,
  "end_offset": <number>,
  "type": "<citation_type>",
  "status": "Correct|Error|Uncertain|NotACitation",
  "errors": ["error1", "error2"],
  "orig": "{orig}",
  "suggested": "<corrected_citation_or_identical_to_orig>",
  "reasoning_summary": "<brief_explanation_of_your_analysis>"
}}
```

**Important Notes:**
- If this is NOT a legal citation, set status to "NotACitation" and type to "other"
- If the citation is correct, set suggested identical to orig
- If uncertain, explain why in reasoning_summary
- Be precise with start_offset and end_offset (character positions from anchor)
- Only include actual Bluebook rule violations in errors array
"""
        
        return prompt
    
    def _extract_citation_context(self, original_text: str, anchor: str, citation: str) -> str:
        """
        Extract context around a citation for better analysis
        """
        try:
            # Find the anchor in the text
            anchor_pattern = re.escape(anchor)
            anchor_match = re.search(anchor_pattern, original_text)
            
            if not anchor_match:
                return f"Context not found for anchor {anchor}"
            
            anchor_start = anchor_match.start()
            
            # Find the citation near the anchor
            citation_pattern = re.escape(citation)
            citation_match = re.search(citation_pattern, original_text[anchor_start:anchor_start+1000])
            
            if not citation_match:
                return f"Citation '{citation}' not found near anchor {anchor}"
            
            citation_start = anchor_start + citation_match.start()
            citation_end = anchor_start + citation_match.end()
            
            # Extract context (200 chars before and after)
            context_start = max(0, citation_start - 200)
            context_end = min(len(original_text), citation_end + 200)
            
            context = original_text[context_start:context_end]
            
            # Highlight the citation in context
            citation_in_context = context[citation_start - context_start:citation_end - context_start]
            highlighted_context = context.replace(citation_in_context, f"[{citation_in_context}]")
            
            return highlighted_context
            
        except Exception as e:
            return f"Error extracting context: {e}"
    
    def _parse_reasoning_response(self, response_text: str, original_citation: Dict[str, Any], debug: bool = False) -> Optional[Dict[str, Any]]:
        """
        Parse the reasoning model's response and extract validated citation
        """
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'(\{.*?\})', response_text, re.DOTALL)
                if json_match:
                    json_content = json_match.group(1)
                else:
                    if debug:
                        print(f"         ❌ No JSON found in response")
                    return None
            
            # Parse JSON
            validated_citation = json.loads(json_content)
            
            # Validate required fields
            required_fields = ['anchor', 'type', 'status', 'orig', 'suggested']
            for field in required_fields:
                if field not in validated_citation:
                    if debug:
                        print(f"         ❌ Missing required field: {field}")
                    return None
            
            # Ensure anchor matches original
            if validated_citation['anchor'] != original_citation.get('anchor', ''):
                validated_citation['anchor'] = original_citation.get('anchor', '')
            
            # Ensure orig matches original
            if validated_citation['orig'] != original_citation.get('orig', ''):
                validated_citation['orig'] = original_citation.get('orig', '')
            
            # Set default values for missing fields
            if 'start_offset' not in validated_citation:
                validated_citation['start_offset'] = original_citation.get('start_offset', 0)
            if 'end_offset' not in validated_citation:
                validated_citation['end_offset'] = original_citation.get('end_offset', 0)
            if 'errors' not in validated_citation:
                validated_citation['errors'] = []
            
            return validated_citation
            
        except json.JSONDecodeError as e:
            if debug:
                print(f"         ❌ JSON parsing error: {e}")
            return None
        except Exception as e:
            if debug:
                print(f"         ❌ Response parsing error: {e}")
            return None
    
    def batch_validate_with_reasoning(
        self, 
        citations: List[Dict[str, Any]], 
        original_text: str,
        effort: ReasoningEffort = ReasoningEffort.MEDIUM,
        batch_size: int = 5,
        debug: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Validate citations in batches to manage API costs and rate limits
        """
        if not citations:
            return []
        
        print(f"📦 Batch validating {len(citations)} citations...")
        
        validated_citations = []
        
        for i in range(0, len(citations), batch_size):
            batch = citations[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(citations) + batch_size - 1) // batch_size
            
            print(f"   📦 Processing batch {batch_num}/{total_batches} ({len(batch)} citations)")
            
            batch_validated = self.validate_citations_with_reasoning(
                batch, original_text, effort, debug
            )
            
            validated_citations.extend(batch_validated)
            
            # Add delay between batches to respect rate limits
            if i + batch_size < len(citations):
                import time
                time.sleep(1)  # 1 second delay between batches
        
        return validated_citations

def main():
    """CLI interface for reasoning citation validator"""
    if len(sys.argv) < 3:
        print("Reasoning Citation Validator")
        print("=" * 40)
        print("Usage:")
        print("  python reasoning_citation_validator.py validate <citations.json> <original_text.txt> [output.json]")
        print("\nOptions:")
        print("  --debug: Enable debug output")
        print("  --effort low|medium|high: Reasoning effort level (default: medium)")
        print("  --batch-size N: Batch size for processing (default: 5)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    debug = "--debug" in sys.argv
    
    # Parse effort level
    effort = ReasoningEffort.MEDIUM
    for i, arg in enumerate(sys.argv):
        if arg == "--effort" and i + 1 < len(sys.argv):
            try:
                effort = ReasoningEffort(sys.argv[i + 1].lower())
            except ValueError:
                print(f"❌ Invalid effort level: {sys.argv[i + 1]}")
                sys.exit(1)
    
    # Parse batch size
    batch_size = 5
    for i, arg in enumerate(sys.argv):
        if arg == "--batch-size" and i + 1 < len(sys.argv):
            try:
                batch_size = int(sys.argv[i + 1])
            except ValueError:
                print(f"❌ Invalid batch size: {sys.argv[i + 1]}")
                sys.exit(1)
    
    if command == "validate":
        if len(sys.argv) < 4:
            print("❌ Citations file and original text file required")
            sys.exit(1)
        
        citations_file = sys.argv[2]
        text_file = sys.argv[3]
        output_file = sys.argv[4] if len(sys.argv) > 4 else None
        
        # Load citations
        try:
            with open(citations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                citations = data.get('citations', []) if isinstance(data, dict) else data
        except Exception as e:
            print(f"❌ Failed to load citations: {e}")
            sys.exit(1)
        
        # Load original text
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                original_text = f.read()
        except Exception as e:
            print(f"❌ Failed to load original text: {e}")
            sys.exit(1)
        
        # Initialize validator
        validator = ReasoningCitationValidator()
        
        # Validate citations
        validated_citations = validator.batch_validate_with_reasoning(
            citations, original_text, effort, batch_size, debug
        )
        
        # Save results
        results = {
            "analysis_summary": {
                "total_citations_processed": len(citations),
                "citations_validated": len(validated_citations),
                "reasoning_effort": effort.value,
                "batch_size": batch_size
            },
            "citations": validated_citations
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"✅ Results saved to: {output_file}")
        else:
            print("\n📊 VALIDATION RESULTS:")
            print(f"   • Total citations processed: {len(citations)}")
            print(f"   • Citations validated: {len(validated_citations)}")
            print(f"   • Reasoning effort: {effort.value}")
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
