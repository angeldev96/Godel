"""
Legal Citation Checker - Analyzes legal documents for Bluebook citation violations
"""
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Add parent directory to path to import from core and config folders
sys.path.append(str(Path(__file__).parent.parent))

from config.config import config, LLMProvider
from llm.llm_client import LLMClient, LLMClientFactory
from llm.token_estimator import TokenEstimator
from core.xml_to_anchored_txt import xml_to_anchored_txt
from core.extract_docx_xml import extract_docx_xml

class LegalCitationChecker:
    """Main legal citation checker with Bluebook compliance analysis"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, 
                 provider: Optional[LLMProvider] = None):
        # Use provided parameters or get from config
        if provider:
            # Use specified provider
            self.client = LLMClient(provider, api_key, model)
            self.provider = provider
        elif api_key:
            # Use provided API key with default provider (Llama)
            self.client = LLMClient(LLMProvider.LLAMA, api_key, model)
            self.provider = LLMProvider.LLAMA
        else:
            # Use task-specific configuration
            model_config = config.get_model_for_task("citation_checking")
            self.provider = model_config["provider"]
            provider_api_key = config.get_api_key(self.provider)
            if provider_api_key:
                self.client = LLMClient(self.provider, provider_api_key, model_config["model"])
            else:
                self.client = None
        
        if self.client:
            print(f"✅ Using {self.provider.value} model: {self.client.model}")
        else:
            print("❌ No API client configured")
        
        self.token_estimator = TokenEstimator(self.client.model if self.client else "llama3.2-3b")
        self.prompt_file = Path(__file__).parent.parent / "config" / "legal_citation_prompt.txt"
        self.default_prompt = self._load_default_prompt()
        
    def _load_default_prompt(self) -> str:
        """Load the default legal citation prompt"""
        if self.prompt_file.exists():
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"⚠️ Warning: Prompt file not found: {self.prompt_file}")
            return "You are a legal citation expert. Analyze the following text for Bluebook citation violations and return results in JSON format."
    
    def setup_api_key(self, provider: LLMProvider, api_key: str, model: Optional[str] = None):
        """Setup API key for the checker"""
        self.client = LLMClient(provider, api_key, model)
        self.provider = provider
        print(f"✅ API key configured for {provider.value} citation checker")
    
    def check_citations_from_docx(self, docx_path: str, output_file: Optional[str] = None, 
                                 debug: bool = False) -> Optional[Dict[str, Any]]:
        """
        Check citations in a DOCX file
        
        Args:
            docx_path: Path to DOCX file
            output_file: Optional output file for results
            debug: Enable debug output
            
        Returns:
            Citation analysis results
        """
        if not self.client:
            print("❌ No API client configured")
            return None
            
        docx_path_obj = Path(docx_path)
        if not docx_path_obj.exists():
            print(f"❌ Document not found: {docx_path}")
            return None
        
        try:
            print(f"📄 Analyzing citations in: {docx_path_obj.name}")
            
            # Step 1: Extract XML from DOCX
            print("🔧 Step 1: Extracting XML...")
            xml_file = extract_docx_xml(str(docx_path_obj))
            if not xml_file:
                print("❌ Failed to extract XML")
                return None
            
            # Step 2: Convert to anchored TXT
            print("🔗 Step 2: Converting to anchored TXT...")
            anchored_txt_file = xml_to_anchored_txt(xml_file)
            if not anchored_txt_file:
                print("❌ Failed to convert to anchored TXT")
                return None
            
            # Step 3: Read anchored text
            with open(anchored_txt_file, 'r', encoding='utf-8') as f:
                anchored_text = f.read()
            
            # Step 4: Check citations
            print("🔍 Step 3: Checking citations...")
            results = self.check_citations_in_text(anchored_text, debug=debug, output_file=output_file)
            
            # Step 5: Save results
            if results and output_file:
                output_path = Path(output_file)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                print(f"✅ Results saved to: {output_path}")
            
            return results
            
        except Exception as e:
            print(f"❌ Citation checking failed: {e}")
            return None
    
    def check_citations_in_text(self, text: str, debug: bool = False, output_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Check citations in text with batching support
        
        Args:
            text: Text with anchor tokens
            debug: Enable debug output
            output_file: Optional output file for results
            
        Returns:
            Citation analysis results
        """
        if not self.client:
            print("❌ No API client configured")
            return None
        
        # Analyze text size and determine if batching is needed
        analysis = self.token_estimator.analyze_text_size(text, self.default_prompt)
        
        if debug:
            print(self.token_estimator.get_debug_info(text, self.default_prompt))
        
        if analysis['needs_batching']:
            print(f"📦 Text requires batching into {analysis['recommended_batches']} batches")
            return self._check_citations_batched(text, analysis, debug, output_file)
        else:
            print("✅ Text fits in single context window")
            return self._check_citations_single(text, debug, output_file)
    
    def _structure_citation_results(self, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure raw citation array into proper results format"""
        total_citations = len(citations)
        citations_with_errors = sum(1 for c in citations if c.get('status') == 'Error')
        citations_correct = total_citations - citations_with_errors
        
        return {
            "analysis_summary": {
                "total_citations_found": total_citations,
                "citations_with_errors": citations_with_errors,
                "citations_correct": citations_correct
            },
            "citations": citations,
            "recommendations": []
        }
    
    def _check_citations_single(self, text: str, debug: bool = False, output_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Check citations in a single API call"""
        import json
        import re
        
        if not self.client:
            print("❌ No API client configured")
            return None
            
        try:
            # Prepare the full prompt
            full_prompt = self.default_prompt + "\n\n" + text
            
            if debug:
                print(f"📤 Sending {len(full_prompt)} characters to LLM...")
            
            # Send to LLM
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a legal citation expert."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=4000  # Increased from 2000 to allow for complete JSON response
            )
            
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']
                
                # Always save the raw LLM output
                raw_output_path = None
                if output_file:
                    raw_output_path = Path(output_file).with_suffix('.raw.txt')
                    with open(raw_output_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    if debug:
                        print(f"💾 Raw LLM output saved to: {raw_output_path}")
                
                if debug:
                    print(f"📄 Full response length: {len(content)} characters")
                    print(f"📄 Response preview: {content[:200]}...")
                    print(f"📄 Response ending: ...{content[-200:]}")
                
                # Robust JSON extraction: find the first valid JSON array
                try:
                    # First, try to extract JSON from markdown code blocks
                    code_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
                    if code_block_match:
                        json_content = code_block_match.group(1)
                        citations = json.loads(json_content)
                        print("✅ Citation analysis completed successfully (extracted from markdown)")
                        # Structure the results properly
                        return self._structure_citation_results(citations)
                    
                    # Try to parse as a JSON array directly
                    if content.strip().startswith('['):
                        # Try to find the matching closing bracket for the array
                        array_match = re.search(r'(\[.*?\])', content, re.DOTALL)
                        if array_match:
                            json_content = array_match.group(1)
                            citations = json.loads(json_content)
                            print("✅ Citation analysis completed successfully (extracted JSON array)")
                            return self._structure_citation_results(citations)
                    
                    # Fallback: try to extract JSON array from anywhere in the content
                    array_match = re.search(r'(\[.*?\])', content, re.DOTALL)
                    if array_match:
                        json_content = array_match.group(1)
                        citations = json.loads(json_content)
                        print("✅ Citation analysis completed successfully (extracted JSON array)")
                        return self._structure_citation_results(citations)
                    
                    # If that fails, try to parse the entire response as JSON
                    results = json.loads(content)
                    print("✅ Citation analysis completed successfully (parsed as JSON)")
                    return results
                except Exception as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    if raw_output_path:
                        print(f"💾 Raw LLM output saved to: {raw_output_path}")
                    if debug:
                        print(f"Raw response: {content}")
                    return None
            else:
                print("❌ No content in API response")
                return None
                
        except Exception as e:
            print(f"❌ Citation checking failed: {e}")
            return None
    
    def _check_citations_batched(self, text: str, analysis: Dict[str, Any], 
                                debug: bool = False, output_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Check citations using batching"""
        try:
            # Split text into batches
            available_tokens = analysis['available_tokens']
            batches = self.token_estimator.split_text_by_anchors(text, available_tokens)
            
            all_results = []
            combined_citations = []
            total_citations = 0
            citations_with_errors = 0
            citations_correct = 0
            
            print(f"🔄 Processing {len(batches)} batches...")
            
            for i, batch in enumerate(batches):
                batch_info = batch.get('batch_info', {})
                anchor_count = batch_info.get('anchor_count', 0)
                print(f"📦 Processing batch {i+1}/{len(batches)} ({anchor_count} anchors)")
                
                batch_text = batch['text']
                batch_results = self._check_citations_single(batch_text, debug, output_file)
                
                if batch_results:
                    all_results.append(batch_results)
                    
                    # Combine citation data
                    if 'citations' in batch_results:
                        combined_citations.extend(batch_results['citations'])
                    
                    # Update summary statistics
                    if 'analysis_summary' in batch_results:
                        summary = batch_results['analysis_summary']
                        total_citations += summary.get('total_citations_found', 0)
                        citations_with_errors += summary.get('citations_with_errors', 0)
                        citations_correct += summary.get('citations_correct', 0)
            
            # Combine all results
            if all_results:
                combined_results = {
                    "analysis_summary": {
                        "total_citations_found": total_citations,
                        "citations_with_errors": citations_with_errors,
                        "citations_correct": citations_correct,
                        "batches_processed": len(batches)
                    },
                    "citations": combined_citations,
                    "recommendations": self._combine_recommendations(all_results)
                }
                
                print("✅ Batched citation analysis completed successfully")
                return combined_results
            else:
                print("❌ No results from any batch")
                return None
                
        except Exception as e:
            print(f"❌ Batched citation checking failed: {e}")
            return None
    
    def _combine_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Combine recommendations from multiple batches"""
        all_recommendations = set()
        
        for result in results:
            if 'recommendations' in result:
                all_recommendations.update(result['recommendations'])
        
        return list(all_recommendations)
    
    def print_results_summary(self, results: Dict[str, Any]):
        """Print a summary of citation checking results"""
        if not results:
            print("❌ No results to display")
            return
        
        print("\n📊 CITATION ANALYSIS RESULTS")
        print("=" * 50)
        
        if 'analysis_summary' in results:
            summary = results['analysis_summary']
            print(f"📈 Summary:")
            print(f"   • Total citations found: {summary.get('total_citations_found', 0)}")
            print(f"   • Citations with errors: {summary.get('citations_with_errors', 0)}")
            print(f"   • Citations correct: {summary.get('citations_correct', 0)}")
            
            if 'batches_processed' in summary:
                print(f"   • Batches processed: {summary['batches_processed']}")
        
        if 'citations' in results:
            citations = results['citations']
            print(f"\n🔍 Citation Details:")
            
            for i, citation in enumerate(citations[:10], 1):  # Show first 10
                status = "❌ ERROR" if citation.get('has_error') else "✅ CORRECT"
                print(f"   {i}. {status} - {citation.get('citation_text', 'Unknown')}")
                if citation.get('has_error'):
                    print(f"      Error: {citation.get('error_description', 'Unknown error')}")
            
            if len(citations) > 10:
                print(f"   ... and {len(citations) - 10} more citations")
        
        if 'recommendations' in results:
            recommendations = results['recommendations']
            if recommendations:
                print(f"\n💡 Recommendations:")
                for rec in recommendations:
                    print(f"   • {rec}")
    
    def check_citations_batched_with_context(self, docx_path: str, output_file: Optional[str] = None, 
                                           debug: bool = False, batch_size: int = 5, 
                                           context_overlap: int = 2) -> Optional[Dict[str, Any]]:
        """
        Check citations using small batches with context windows for better accuracy
        
        Args:
            docx_path: Path to DOCX file
            output_file: Optional output file for results
            debug: Enable debug output
            batch_size: Number of paragraphs per batch
            context_overlap: Number of paragraphs to overlap between batches
            
        Returns:
            Citation analysis results
        """
        try:
            # Extract XML and convert to anchored TXT
            xml_file = extract_docx_xml(docx_path)
            if not xml_file:
                return None
            
            anchored_txt_file = xml_to_anchored_txt(xml_file)
            if not anchored_txt_file:
                return None
            
            # Read anchored text
            with open(anchored_txt_file, 'r', encoding='utf-8') as f:
                anchored_text = f.read()
            
            # Split into paragraphs
            paragraphs = self._split_into_paragraphs(anchored_text)
            
            if debug:
                print(f"📄 Total paragraphs: {len(paragraphs)}")
                print(f"📦 Batch size: {batch_size}")
                print(f"🔄 Context overlap: {context_overlap}")
            
            # Process in batches with context windows
            all_citations = []
            batch_results = []
            
            for i in range(0, len(paragraphs), batch_size - context_overlap):
                # Create context window
                start_idx = max(0, i - context_overlap)
                end_idx = min(len(paragraphs), i + batch_size)
                
                # Build context window text
                context_text = "\n".join(paragraphs[start_idx:end_idx])
                
                if debug:
                    print(f"\n📦 Processing batch {i//(batch_size - context_overlap) + 1}")
                    print(f"   Paragraphs {start_idx+1}-{end_idx} (context window)")
                    print(f"   Context length: {len(context_text)} characters")
                
                # Process this batch
                batch_citations = self._check_citations_single(context_text, debug, None)
                
                if batch_citations:
                    # Filter citations to only include those from the target paragraphs (not context)
                    target_citations = self._filter_citations_to_target_paragraphs(
                        batch_citations, paragraphs, start_idx, end_idx, i, batch_size
                    )
                    
                    if target_citations:
                        all_citations.extend(target_citations)
                        batch_results.append({
                            'batch_num': i//(batch_size - context_overlap) + 1,
                            'paragraphs': f"{i+1}-{min(i+batch_size, len(paragraphs))}",
                            'citations_found': len(target_citations)
                        })
                        
                        if debug:
                            print(f"   ✅ Found {len(target_citations)} citations")
                    else:
                        if debug:
                            print(f"   ⚠️  No citations in target paragraphs")
                else:
                    if debug:
                        print(f"   ❌ Batch processing failed")
            
            # Validate and resolve inconsistencies
            if all_citations:
                validated_citations = self._validate_citations(all_citations, debug)
                
                # Create final results
                results = {
                    "analysis_summary": {
                        "total_citations_found": len(validated_citations),
                        "citations_with_errors": sum(1 for c in validated_citations if c.get('status') == 'Error'),
                        "citations_correct": sum(1 for c in validated_citations if c.get('status') == 'Correct'),
                        "batches_processed": len(batch_results),
                        "total_batches": (len(paragraphs) + batch_size - context_overlap - 1) // (batch_size - context_overlap)
                    },
                    "citations": validated_citations,
                    "batch_summary": batch_results
                }
                
                # Save results
                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2)
                    print(f"✅ Results saved to: {output_file}")
                
                return results
            else:
                print("❌ No citations found in document")
                return None
                
        except Exception as e:
            print(f"❌ Batched citation checking failed: {e}")
            return None
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split anchored text into individual paragraphs"""
        # Split by anchor tags
        import re
        paragraphs = re.split(r'(⟦P-\d+⟧)', text)
        
        # Combine anchor tags with their content
        result = []
        for i in range(0, len(paragraphs), 2):
            if i + 1 < len(paragraphs):
                result.append(paragraphs[i] + paragraphs[i + 1])
            else:
                result.append(paragraphs[i])
        
        return [p.strip() for p in result if p.strip()]
    
    def _filter_citations_to_target_paragraphs(self, citations: Union[List[Dict], Dict], paragraphs: List[str], 
                                             context_start: int, context_end: int, 
                                             target_start: int, target_size: int) -> List[Dict]:
        """Filter citations to only include those from target paragraphs (not context)"""
        # Handle both list and single dict inputs
        if isinstance(citations, dict):
            citations = [citations]
        elif not isinstance(citations, list):
            return []
        
        target_citations = []
        
        for citation in citations:
            anchor = citation.get('anchor', '')
            if not anchor:
                continue
                
            # Extract paragraph number from anchor
            try:
                para_num = int(anchor.split('-')[1])
                # Adjust for 1-based indexing
                para_idx = para_num - 1
                
                # Check if this citation is in the target range (not context)
                if target_start <= para_idx < target_start + target_size:
                    target_citations.append(citation)
            except (ValueError, IndexError):
                # If we can't parse the anchor, include it
                target_citations.append(citation)
        
        return target_citations
    
    def _validate_citations(self, citations: List[Dict], debug: bool = False) -> List[Dict]:
        """
        Second-stage validation using a more sophisticated model to resolve inconsistencies
        """
        if not citations:
            return []
        
        if debug:
            print(f"\n🔍 Validating {len(citations)} citations...")
        
        # Group citations by anchor to find duplicates/inconsistencies
        citation_groups = {}
        for citation in citations:
            anchor = citation.get('anchor', '')
            if anchor not in citation_groups:
                citation_groups[anchor] = []
            citation_groups[anchor].append(citation)
        
        validated_citations = []
        
        for anchor, group in citation_groups.items():
            if len(group) == 1:
                # Single citation, no inconsistency
                validated_citations.append(group[0])
            else:
                # Multiple citations for same anchor - need validation
                if debug:
                    print(f"   ⚠️  Found {len(group)} citations for {anchor}")
                
                # Use validation prompt to resolve
                resolved_citation = self._resolve_citation_inconsistency(group, debug)
                if resolved_citation:
                    validated_citations.append(resolved_citation)
                else:
                    # If validation fails, use the first one
                    validated_citations.append(group[0])
        
        if debug:
            print(f"✅ Validation complete: {len(validated_citations)} citations")
        
        return validated_citations
    
    def _resolve_citation_inconsistency(self, citations: List[Dict], debug: bool = False) -> Optional[Dict]:
        """
        Use a sophisticated validation prompt to resolve citation inconsistencies
        """
        # Create a separate client for validation using task-specific configuration
        try:
            validation_client = LLMClientFactory.create_client_for_task("citation_validation")
        except Exception as e:
            if debug:
                print(f"   ⚠️  Could not create validation client: {e}")
            return citations[0] if citations else None
        
        # Create validation prompt
        validation_prompt = self._create_validation_prompt(citations)
        
        try:
            response = validation_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a legal citation expert specializing in Bluebook validation."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']
                
                if debug:
                    print(f"   📄 Validation response: {content[:200]}...")
                
                # Parse validation response
                try:
                    import json
                    result = json.loads(content)
                    return result
                except json.JSONDecodeError:
                    if debug:
                        print(f"   ❌ Failed to parse validation response")
                    return citations[0]
            else:
                return citations[0]
                
        except Exception as e:
            if debug:
                print(f"   ❌ Validation failed: {e}")
            return citations[0]
    
    def _create_validation_prompt(self, citations: List[Dict]) -> str:
        """Create a sophisticated validation prompt for resolving citation inconsistencies"""
        
        prompt = f"""
You are a legal citation expert. Multiple analyses have been performed on the same citation, and you need to determine which one is correct.

## CITATION ANALYSES TO VALIDATE:

"""
        
        for i, citation in enumerate(citations, 1):
            prompt += f"""
ANALYSIS {i}:
- Anchor: {citation.get('anchor', 'N/A')}
- Type: {citation.get('type', 'N/A')}
- Status: {citation.get('status', 'N/A')}
- Original: {citation.get('orig', 'N/A')}
- Suggested: {citation.get('suggested', 'N/A')}
- Errors: {citation.get('errors', [])}
"""
        
        prompt += """
## TASK:
Review all analyses above and determine which one is most accurate according to Bluebook rules. Consider:
1. Citation type identification
2. Error detection accuracy
3. Suggested corrections
4. Overall Bluebook compliance

## OUTPUT FORMAT:
Return only a JSON object with the most accurate analysis:

```json
{
  "anchor": "P-XXXXX",
  "start_offset": X,
  "end_offset": X,
  "type": "citation_type",
  "status": "Correct|Error|Uncertain",
  "errors": ["error1", "error2"],
  "orig": "original_citation",
  "suggested": "corrected_citation"
}
```

If none of the analyses are correct, provide your own corrected analysis.
"""
        
        return prompt

def main():
    """Main CLI interface for legal citation checker"""
    if len(sys.argv) < 2:
        print("Legal Citation Checker")
        print("=" * 40)
        print("Usage:")
        print("  python legal_citation_checker.py check <docx_file> [output.json]")
        print("  python legal_citation_checker.py check-text <text_file> [output.json]")
        print("\nOptions:")
        print("  --debug: Enable debug output")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    debug = "--debug" in sys.argv
    
    checker = LegalCitationChecker()
    
    if command == "check":
        if len(sys.argv) < 3:
            print("❌ DOCX file required")
            sys.exit(1)
        
        docx_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        results = checker.check_citations_from_docx(docx_file, output_file, debug)
        if results:
            checker.print_results_summary(results)
    
    elif command == "check-text":
        if len(sys.argv) < 3:
            print("❌ Text file required")
            sys.exit(1)
        
        text_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        # Read text file
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"❌ Failed to read text file: {e}")
            sys.exit(1)
        
        results = checker.check_citations_in_text(text, debug, output_file)
        if results:
            checker.print_results_summary(results)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                print(f"✅ Results saved to: {output_file}")
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 