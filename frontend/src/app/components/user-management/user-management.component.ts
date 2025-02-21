import { Component, inject } from '@angular/core';
import { AddUserModalComponent } from './add-user-modal/add-user-modal.component';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ServicesService } from '../../services.service';
import { Router } from '@angular/router';

// First, update the ContractDocument interface to include analysisResult
interface ContractDocument {
  id?: string;
  fileName: string;
  uploadDate: Date;
  lastUpdated: Date;
  type: string;
  status: string;
  extractedData?: any;
  analysisResult?: any;  // Add this field
}

@Component({
  selector: 'app-user-management',
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.scss'],
  standalone: false
})
export class UserManagementComponent {
  isPopupVisible = false;
  uploadForm!: FormGroup;
  selectedFiles: File[] = [];
  selectedFiles_1: any;
  loadershow: boolean = false;
  extractedValue: any;
  showCategory: boolean = false;
  contracts: ContractDocument[] = [];
  extractionResults: any;
  fileName: string = '';

  constructor(
    private fb: FormBuilder,
    private apiService: ServicesService,
    private router: Router
  ) {
    this.uploadForm = this.fb.group({
      analysisType: [''],
    });
  }

  readonly dialog = inject(MatDialog);
  users = [
    { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Admin' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'User' }
  ];

  displayedColumns: string[] = ['id', 'name', 'email', 'role', 'actions'];

  // Modified onSubmit method with proper extraction data handling
  onSubmit() {
    if (this.extractedValue) {
      const analysisType = this.uploadForm.value.analysisType;
      
      if (analysisType === 'custom_analysis') {
        this.router.navigate(['/Analytics']);
        return;
      }

      this.extractedValue.type = analysisType;
      this.extractedValue.custom_query = '';
      this.loadershow = true; // Show loader before API call

      this.apiService.analyze(this.extractedValue).subscribe({
        next: (res: any) => {
          if (res) {
            // Find the current contract and update it with the analysis result
            const currentContract = this.contracts.find(c => 
              c.fileName === this.selectedFiles_1.name
            );
            
            if (currentContract) {
              currentContract.analysisResult = res;
              currentContract.type = analysisType;
              currentContract.lastUpdated = new Date();
              
              // Update localStorage
              localStorage.setItem('contracts', JSON.stringify(this.contracts));
            }

            // Store the result and navigate
            const analysisData = {
              type: analysisType,
              result: res,
              fileName: this.selectedFiles_1.name
            };
            
            localStorage.setItem('current_analysis', JSON.stringify(analysisData));
            
            // Add debugging for information extraction
            if (analysisType === 'information_extraction') {
              console.log('Saving extraction data:', analysisData);
              
              // Format data specifically for the ExtractionComponent
              const extractionData = {
                'Information Extraction': {
                  results: this.convertToExtractionResults(res)
                }
              };
              
              // Save in the expected format for the extraction component
              localStorage.setItem('extraction', JSON.stringify(extractionData));
            }
            
            // Navigate based on analysis type
            switch (analysisType) {
              case 'contract_review':
              case 'contract_summary':
                this.router.navigate(['/contract-review']);
                break;
              case 'legal_research':
                this.router.navigate(['/legal-research']);
                break;
              case 'risk_assessment':
                this.router.navigate(['/risk-assessment']);
                break;
              case 'information_extraction':
                this.router.navigate(['/extraction']);
                break;
              default:
                console.warn('Unhandled analysis type:', analysisType);
                break;
            }
          }
        },
        error: (error) => {
          console.error('Analysis failed:', error);
          this.loadershow = false;
        }
      });
    }
  }

  // Update the convertToExtractionResults method in UserManagementComponent
  private convertToExtractionResults(result: any): any[] {
    // Handle case where result itself is nested with "Information Extraction" key
    if (result && typeof result === 'object' && result['Information Extraction']) {
      result = result['Information Extraction'];
      
      // If it has a results array, use that directly
      if (Array.isArray(result.results)) {
        return result.results;
      }
      
      // Otherwise, continue with the result itself
      result = result.results || result;
    }
    
    if (Array.isArray(result)) {
      // If already an array, ensure each item has the right structure
      return result.map(item => {
        if (typeof item === 'object' && item !== null) {
          return {
            term: item.term || 'Unknown',
            // Convert any object values to JSON strings to prevent [object Object] display
            extracted_value: typeof item.extracted_value === 'object' ? 
              JSON.stringify(item.extracted_value) : 
              String(item.extracted_value || ''),
            timestamp: item.timestamp || new Date().toISOString()
          };
        } else {
          return {
            term: 'Unknown',
            extracted_value: String(item),
            timestamp: new Date().toISOString()
          };
        }
      });
    } else if (typeof result === 'object' && result !== null) {
      // If it's an object, convert key-value pairs
      return Object.entries(result).map(([key, value]) => ({
        term: key,
        // Convert any object values to JSON strings
        extracted_value: typeof value === 'object' ? 
          JSON.stringify(value) : 
          String(value),
        timestamp: new Date().toISOString()
      }));
    } else {
      // Fallback for unknown formats
      return [{
        term: 'Result',
        extracted_value: String(result),
        timestamp: new Date().toISOString()
      }];
    }
  }

  togglePopup() {
    this.isPopupVisible = !this.isPopupVisible;
  }

  openDialog() {
    const dialogRef = this.dialog.open(AddUserModalComponent, {
      height: '400px',
      width: '600px',
    });
    
    dialogRef.afterClosed().subscribe(result => {
      console.log(`Dialog result: ${result}`);
    });
  }

  fileUpload(e: any) {
    console.log(e);
  }

  uploadFiles() {
    if (this.selectedFiles.length === 0) {
      alert("No files selected!");
      return;
    }

    const formData = new FormData();
    this.selectedFiles.forEach(file => formData.append('file', file));

    console.log('Uploading...', formData);
    alert('Files uploaded successfully!');
  }

  onFileSelected(event: any) {
    this.selectedFiles_1 = event.target.files[0];
    const formData = new FormData();
    formData.append('file', this.selectedFiles_1);
    
    // Check if file already exists
    const existingContract = this.contracts.find(c => c.fileName === this.selectedFiles_1.name);
    
    this.apiService.upload_file(formData).subscribe({
      next: (res: any) => {
        if (res) {
          localStorage.setItem("extractionInfo", JSON.stringify(res));
          this.extractedValue = res;
          this.showCategory = true;
          this.loadershow = true;

          // Update or add new contract
          const contractDoc: ContractDocument = {
            fileName: this.selectedFiles_1.name,
            uploadDate: existingContract ? existingContract.uploadDate : new Date(),
            lastUpdated: new Date(),
            type: this.uploadForm.value.analysisType || 'Unknown',
            status: 'Active',
            extractedData: res
          };

          if (existingContract) {
            const index = this.contracts.findIndex(c => c.fileName === this.selectedFiles_1.name);
            this.contracts[index] = contractDoc;
          } else {
            this.contracts.push(contractDoc);
          }

          // Save to localStorage for persistence
          localStorage.setItem('contracts', JSON.stringify(this.contracts));
        }
      },
      error: (error) => {
        console.error('File upload failed:', error);
        this.loadershow = false;
      }
    });
  }
  
  // Updated viewContract method that formats extraction data properly
  viewContract(contract: ContractDocument) {
    if (contract.analysisResult) {
      try {
        // Store current analysis state
        const analysisData = {
          type: contract.type,
          result: contract.analysisResult,
          fileName: contract.fileName
        };
        
        localStorage.setItem('current_analysis', JSON.stringify(analysisData));
        
        // Format and store extraction data if needed
        if (contract.type === 'information_extraction') {
          console.log('Viewing extraction data:', analysisData);
          
          // Format data specifically for the ExtractionComponent
          const extractionData = {
            'Information Extraction': {
              results: this.convertToExtractionResults(contract.analysisResult)
            }
          };
          
          // Save in the expected format for the extraction component
          localStorage.setItem('extraction', JSON.stringify(extractionData));
        }

        // Navigate based on the contract type
        switch (contract.type) {
          case 'contract_review':
          case 'contract_summary':
            this.router.navigate(['/contract-review']);
            break;
          case 'legal_research':
            this.router.navigate(['/legal-research']);
            break;
          case 'risk_assessment':
            this.router.navigate(['/risk-assessment']);
            break;
          case 'information_extraction':
            this.router.navigate(['/extraction']);
            break;
          default:
            console.warn('Unknown contract type:', contract.type);
            this.router.navigate(['/extraction']);
            break;
        }
      } catch (error) {
        console.error('Error viewing contract:', error);
        alert('Error viewing contract. Please try again.');
      }
    } else {
      alert('No analysis results available for this contract. Please run an analysis first.');
    }
  }

  deleteContract(contract: ContractDocument) {
    if (confirm(`Are you sure you want to delete "${contract.fileName}"?`)) {
      const index = this.contracts.findIndex(c => c.fileName === contract.fileName);
      if (index > -1) {
        // Remove from array
        this.contracts.splice(index, 1);
        
        // Update localStorage
        localStorage.setItem('contracts', JSON.stringify(this.contracts));
        
        // Clear related localStorage items if they match this contract
        const extractionInfo = localStorage.getItem('extractionInfo');
        if (extractionInfo) {
          const parsedInfo = JSON.parse(extractionInfo);
          if (parsedInfo.fileName === contract.fileName) {
            localStorage.removeItem('extractionInfo');
          }
        }
        
        // Also clear extraction data if it matches
        const currentAnalysis = localStorage.getItem('current_analysis');
        if (currentAnalysis) {
          const analysisData = JSON.parse(currentAnalysis);
          if (analysisData.fileName === contract.fileName) {
            localStorage.removeItem('current_analysis');
            localStorage.removeItem('extraction'); // Also remove extraction-specific data
          }
        }
        
        // Clear other analysis types if they match
        const analysisTypes = [
          'contract_review',
          'legal_research',
          'risk_assessment',
          'extraction'
        ];
        
        analysisTypes.forEach(type => {
          const storedData = localStorage.getItem(type);
          if (storedData) {
            const parsedData = JSON.parse(storedData);
            if (parsedData.fileName === contract.fileName) {
              localStorage.removeItem(type);
            }
          }
        });
      }
    }
  }

  ngOnInit() {
    // Load saved contracts
    const savedContracts = localStorage.getItem('contracts');
    if (savedContracts) {
      this.contracts = JSON.parse(savedContracts);
    }
    
    // Retrieve the current analysis data
    const currentAnalysis = localStorage.getItem('current_analysis');
    if (currentAnalysis) {
      const analysisData = JSON.parse(currentAnalysis);
      if (analysisData.type === 'information_extraction') {
        // Display the extraction data
        this.extractionResults = analysisData.result;
        this.fileName = analysisData.fileName;
        console.log('Loaded extraction results:', this.extractionResults);
      }
    }
  }
}