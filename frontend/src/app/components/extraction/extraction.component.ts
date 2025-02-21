import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';

interface ExtractionResult {
  term: string;
  extracted_value: string;
  timestamp: string;
  category?: string;
}

interface ExtractionData {
  'Information Extraction': {
    results: ExtractionResult[];
  }
}

@Component({
  selector: 'app-extraction',
  imports: [CommonModule],
  templateUrl: './extraction.component.html',
  styleUrl: './extraction.component.scss',
  standalone: true,
  animations: [
    trigger('expandCollapse', [
      state('void', style({ 
        height: '0',
        overflow: 'hidden'
      })),
      state('*', style({ 
        height: '*',
        overflow: 'hidden'
      })),
      transition('void <=> *', animate('300ms ease-in-out'))
    ])
  ]
})
export class ExtractionComponent implements OnInit {
  extractionData: ExtractionResult[] = [];
  loading: boolean = true;
  error: string | null = null;
  
  // Define categories and their associated terms
  contractSections: {[key: string]: string[]} = {
    "Contract Metadata": [
      "Contract Name", "Agreement Type", "Country of agreement", "Contract Details",
      "Entity Name", "Counterparty Name", "Summary", "Department of Contract Owner",
      "SPOC", "Agreement Group", "Family Agreement", "Family Documents Present",
      "Family Hierarchy", "Scanned"
    ],
    "Key Dates and Duration": [
      "Signature by:", "Effective Date", "Contract Start Date", "Contract Duration",
      "Contract End Date", "Contingent Contract", "Perpetual Contract", "SLA",
      "Stamping Date", "Franking Date", "Franking Date_Availablity"
    ],
    "Legal Framework": [
      "Governing Law", "Dispute Resolution", "Place of Courts", "Court Jurisdiction",
      "Place of Arbitration", "Arbitration Institution", "Number of Arbitrators",
      "Seat of Arbitration", "Venue of Arbitration"
    ],
    "Liability and Indemnification": [
      "Legal Action Rights with counterparty", "Counterparty - liability cap",
      "Counterparty - liability limitation summary", "Indemnification",
      "Indemnification Summary", "Counterparty - liquidated damages",
      "Counterparty - damages summary", "Penalties",
      "Penal interest rate and other late payment charges"
    ],
    "Assignment and Termination": [
      "assignment rights", "Counterparty assignment rights",
      "Counterparty - assignment summary", "Can  terminate for Convenience?",
      "If yes, number of notice days?", "Can Counterparty terminate for Convenience?",
      "Counterparty - If yes, number of notice days?", "Counterparty - termination summary"
    ],
    "Contract Renewal and Lock-in": [
      "Provision for lock-in period", "Period of lock in.", "Lock-in summary",
      "Counterparty  - Change of Control Provision", "Auto-renewal provision",
      "Notice period (in days) to stop auto renewal", "Renewal Option Notice Start Date",
      "Renewal Option Notice End Date", "Auto-renewal provision summary"
    ],
    "Special Clauses": [
      "Acceleration clause applicable to ", "Acceleration clause applicable to Counterparty",
      "Acceleration clause - summary", "Exclusivity provision", "Scope", "Territory",
      "Carve-outs", "Exclusivity Period (Start Date)", "Exclusivity Period (End Date)",
      "Available to ", "Available to Counterparty", "Audit Rights - Summary"
    ],
    "Intellectual Property and Compliance": [
      "Copyright", "Patent", "Trademark", "Other",
      "ABAC/FCPA provision", "ABAC/FCPA provision - summary"
    ],
    "Financial Terms": [
      "Receive or Pay", "Currency", "Total Contract Value", "Fixed Fee",
      "Security Deposit / Bank Guarantee", "Fuel surcharges", "Advance payment period",
      "Advance payment Amount", "Term for Refund of Security Deposit", "Incentive",
      "Revenue Share", "Commission Percentage", "Minimum Guarantee", "Variable Fee",
      "Fee-Other", "Payment Type", "Payment Schedule (in days)", "Payment Terms / Details",
      "Milestones", "Payment to Affiliates / Agency", "Fee Escalation", "Stamp Duty Share"
    ],
    "Confidentiality and Data Protection": [
      "Confidentiality", "Residual Confidentiality", "Exceptions to confidentiality",
      "Term (In months)", "Data Privacy Provision", "Data Privacy Summary"
    ],
    "Additional Terms and Conditions": [
      "Insurance coverage for ", "Insurance coverage for Counterparty",
      "Subcontracting rights for the  Counterpart", "Defect liability period",
      "Performance Guarantee", "Conflicts of Interests", "Force Majeure",
      "Insurance coverage", "Representation and Warranties", "Non-Compete",
      "Non-Solicitation", "Waiver", "Severability", "Survival"
    ],
    "Document Quality": [
      "Handwritten Comments", "Missing Pages", "Missing Signatures", "Review Comments (if any)"
    ]
  };
  
  // Get just the category names for easy iteration
  get categories(): string[] {
    return Object.keys(this.contractSections);
  }
  
  // Track which sections are expanded
  expandedSections: {[key: string]: boolean} = {};

  ngOnInit(): void {
    // Initialize all sections as collapsed
    this.categories.forEach(category => {
      this.expandedSections[category] = false;
    });
    
    this.loadExtractionData();
  }

  loadExtractionData(): void {
    this.loading = true;
    this.error = null;
    
    try {
      // First try to get data from 'extraction' key (preferred format)
      let rawData = localStorage.getItem('extraction');
      
      // If no data found, try current_analysis as fallback
      if (!rawData) {
        console.log('No data in "extraction", checking "current_analysis"...');
        const currentAnalysis = localStorage.getItem('current_analysis');
        
        if (currentAnalysis) {
          const analysisData = JSON.parse(currentAnalysis);
          
          if (analysisData.type === 'information_extraction' && analysisData.result) {
            console.log('Found extraction data in current_analysis, converting format...');
            
            // Convert and format the extraction data
            let results: ExtractionResult[] = [];
            const result = analysisData.result;
            
            // Handle different possible formats
            if (Array.isArray(result)) {
              results = result.map(item => this.formatExtractionItem(item));
            } else if (typeof result === 'object' && result !== null) {
              // Handle categorized data
              if (result['Information Extraction'] && 
                  result['Information Extraction'].results) {
                results = this.formatResultsWithCategories(result['Information Extraction'].results);
              } else {
                // If data isn't categorized, handle as key-value pairs
                results = Object.entries(result).map(([term, value]) => ({
                  term,
                  extracted_value: typeof value === 'object' ? 
                    JSON.stringify(value) : String(value),
                  timestamp: new Date().toISOString(),
                  category: this.findCategoryForTerm(term) // Try to assign category based on term
                }));
              }
            } else {
              // Simple value
              results = [{
                term: 'Result',
                extracted_value: String(result),
                timestamp: new Date().toISOString(),
                category: 'Other'
              }];
            }
            
            // Create properly formatted data
            const extractionData = {
              'Information Extraction': {
                results: results
              }
            };
            
            // Save in the correct format for next time
            localStorage.setItem('extraction', JSON.stringify(extractionData));
            rawData = JSON.stringify(extractionData);
          }
        }
      }
      
      if (!rawData) {
        console.warn('No extraction data found in localStorage');
        this.error = 'No extraction data found. Please run an extraction analysis first.';
        this.extractionData = [];
        this.loading = false;
        return;
      }

      console.log('Parsing extraction data:', rawData);
      
      try {
        const parsedData: ExtractionData = JSON.parse(rawData);
        
        if (parsedData['Information Extraction']?.results) {
          // Process and categorize the results
          this.extractionData = this.formatResultsWithCategories(
            parsedData['Information Extraction'].results
          );
          console.log('Loaded extraction data successfully:', this.extractionData);
        } else {
          console.error('Invalid extraction data format:', parsedData);
          this.error = 'Invalid data format. Please try running the extraction again.';
          this.extractionData = [];
        }
      } catch (parseError) {
        console.error('Error parsing JSON data:', parseError);
        this.error = 'Invalid data format. Please try running the extraction again.';
        this.extractionData = [];
      }
    } catch (error) {
      console.error('Error loading extraction data:', error);
      this.error = 'Error loading extraction data. Please try again.';
      this.extractionData = [];
    } finally {
      this.loading = false;
    }
  }

  // Format results and assign categories
  private formatResultsWithCategories(results: any[]): ExtractionResult[] {
    return results.map(item => {
      const formattedItem = this.formatExtractionItem(item);
      
      // Assign a category if not already assigned
      if (!formattedItem.category) {
        formattedItem.category = this.findCategoryForTerm(formattedItem.term);
      }
      
      return formattedItem;
    });
  }

  // Helper method to ensure consistent item format and handle nested objects
  private formatExtractionItem(item: any): ExtractionResult {
    if (typeof item !== 'object' || item === null) {
      return {
        term: 'Unknown',
        extracted_value: String(item),
        timestamp: new Date().toISOString(),
        category: 'Additional Terms and Conditions'
      };
    }
    
    return {
      term: item.term || 'Unknown',
      extracted_value: typeof item.extracted_value === 'object' ? 
        JSON.stringify(item.extracted_value) : 
        String(item.extracted_value || ''),
      timestamp: item.timestamp || new Date().toISOString(),
      category: item.category || null
    };
  }

  // Assign a category based on exact term match in contractSections
  private findCategoryForTerm(term: string): string {
    // First try to find an exact match
    for (const [category, terms] of Object.entries(this.contractSections)) {
      if (terms.includes(term)) {
        return category;
      }
    }
    
    // If no exact match, try to find a partial match
    const termLower = term.toLowerCase();
    for (const [category, terms] of Object.entries(this.contractSections)) {
      for (const categoryTerm of terms) {
        if (termLower.includes(categoryTerm.toLowerCase()) || 
            categoryTerm.toLowerCase().includes(termLower)) {
          return category;
        }
      }
    }
    
    // Finally, try to match by keywords if still no match
    if (termLower.includes('party') || termLower.includes('contract name') || termLower.includes('agreement')) {
      return 'Contract Metadata';
    } else if (termLower.includes('date') || termLower.includes('duration') || termLower.includes('start')) {
      return 'Key Dates and Duration';
    } else if (termLower.includes('law') || termLower.includes('jurisdiction') || termLower.includes('arbitration')) {
      return 'Legal Framework';
    } else if (termLower.includes('liabil') || termLower.includes('indemn') || termLower.includes('damage')) {
      return 'Liability and Indemnification';
    } else if (termLower.includes('assign') || termLower.includes('terminat')) {
      return 'Assignment and Termination';
    } else if (termLower.includes('renewal') || termLower.includes('lock-in') || termLower.includes('auto-')) {
      return 'Contract Renewal and Lock-in';
    } else if (termLower.includes('clause') || termLower.includes('exclusiv') || termLower.includes('audit')) {
      return 'Special Clauses';
    } else if (termLower.includes('ip') || termLower.includes('patent') || termLower.includes('copyright')) {
      return 'Intellectual Property and Compliance';
    } else if (termLower.includes('pay') || termLower.includes('fee') || termLower.includes('price') || termLower.includes('currency')) {
      return 'Financial Terms';
    } else if (termLower.includes('confident') || termLower.includes('privacy') || termLower.includes('data')) {
      return 'Confidentiality and Data Protection';
    } else if (termLower.includes('document') || termLower.includes('quality') || termLower.includes('signature')) {
      return 'Document Quality';
    }
    
    // Default category
    return 'Additional Terms and Conditions';
  }

  // Get results for a specific category
  getResultsForCategory(category: string): ExtractionResult[] {
    return this.extractionData.filter(item => item.category === category);
  }

  // Toggle section expansion
  toggleSection(category: string): void {
    this.expandedSections[category] = !this.expandedSections[category];
  }

  // Check if a section is expanded
  isSectionExpanded(category: string): boolean {
    return this.expandedSections[category];
  }

  // Check if a section has any results
  hasCategoryResults(category: string): boolean {
    return this.getResultsForCategory(category).length > 0;
  }

  refreshData(): void {
    this.loadExtractionData();
  }
}