"""
Legal Citation Checker - Analyzes legal documents for Bluebook citation violations
"""
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path to import from core and config folders
sys.path.append(str(Path(__file__).parent.parent))

from config.config import config
from llm.llm_client import LLMClient
from llm.token_estimator import TokenEstimator
from core.xml_to_anchored_txt import xml_to_anchored_txt
from core.extract_docx_xml import extract_docx_xml

class LegalCitationChecker:
    """Main legal citation checker with Bluebook compliance analysis"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama3.2-3b"):
        # Use provided API key or get from config
        loaded_key = None
        if api_key:
            self.client = LLMClient(api_key)
            loaded_key = api_key
        elif config.is_configured() and config.api_key:
            self.client = LLMClient(config.api_key)
            loaded_key = config.api_key
        else:
            self.client = None
            loaded_key = None
        if loaded_key:
            print(f"[DEBUG] Loaded API key: ...{loaded_key[-4:]}")
        else:
            print("[DEBUG] No API key loaded in LegalCitationChecker")
        self.token_estimator = TokenEstimator(model)
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
    
    def setup_api_key(self, api_key: str):
        """Setup API key for the checker"""
        self.client = LLMClient(api_key)
        print("✅ API key configured for citation checker")
    
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
            results = self.check_citations_in_text(anchored_text, debug=debug)
            
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
    
    def check_citations_in_text(self, text: str, debug: bool = False) -> Optional[Dict[str, Any]]:
        """
        Check citations in text with batching support
        
        Args:
            text: Text with anchor tokens
            debug: Enable debug output
            
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
            return self._check_citations_batched(text, analysis, debug)
        else:
            print("✅ Text fits in single context window")
            return self._check_citations_single(text, debug)
    
    def _check_citations_single(self, text: str, debug: bool = False) -> Optional[Dict[str, Any]]:
        """Check citations in a single API call"""
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
                
                if debug:
                    print(f"📄 Full response length: {len(content)} characters")
                    print(f"📄 Response preview: {content[:200]}...")
                    print(f"📄 Response ending: ...{content[-200:]}")
                
                # Parse JSON response - handle cases where LLM adds explanatory text
                try:
                    # First try to parse the entire response as JSON
                    results = json.loads(content)
                    print("✅ Citation analysis completed successfully")
                    return results
                except json.JSONDecodeError as e:
                    if debug:
                        print(f"❌ Initial JSON parse failed: {e}")
                    
                    # If that fails, try to extract JSON from the response
                    try:
                        # Look for JSON content between ```json and ``` markers
                        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                        if json_match:
                            json_content = json_match.group(1)
                            if debug:
                                print(f"📄 Extracted JSON from code block, length: {len(json_content)}")
                            results = json.loads(json_content)
                            print("✅ Citation analysis completed successfully (extracted from code block)")
                            return results
                        
                        # Look for JSON content starting with { and ending with }
                        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                        if json_match:
                            json_content = json_match.group(1)
                            if debug:
                                print(f"📄 Extracted JSON from response, length: {len(json_content)}")
                                print(f"📄 JSON preview: {json_content[:200]}...")
                                print(f"📄 JSON ending: ...{json_content[-200:]}")
                            results = json.loads(json_content)
                            print("✅ Citation analysis completed successfully (extracted JSON)")
                            return results
                        
                        print(f"❌ Failed to extract JSON from response")
                        if debug:
                            print(f"Raw response: {content}")
                        return None
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse extracted JSON: {e}")
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
                                debug: bool = False) -> Optional[Dict[str, Any]]:
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
                batch_results = self._check_citations_single(batch_text, debug)
                
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
        
        results = checker.check_citations_in_text(text, debug)
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