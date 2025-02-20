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

  // In the onSubmit method, update how we store the analysis result
  onSubmit() {
    if (this.extractedValue) {
      const analysisType = this.uploadForm.value.analysisType;
      
      if (analysisType === 'custom_analysis') {
        this.router.navigate(['/Analytics']);
        return;
      }

      this.extractedValue.type = analysisType;
      this.extractedValue.custom_query = '';

      this.apiService.analyze(this.extractedValue).subscribe({
        next: (res: any) => {
          if (res) {
            this.loadershow = true;
            
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
            switch (analysisType) {
              case 'contract_review':
              case 'contract_summary':
                localStorage.setItem('current_analysis', JSON.stringify({
                  type: analysisType,
                  result: res,
                  fileName: this.selectedFiles_1.name
                }));
                this.router.navigate(['/contract-review']);
                break;

              case 'legal_research':
                localStorage.setItem('current_analysis', JSON.stringify({
                  type: analysisType,
                  result: res,
                  fileName: this.selectedFiles_1.name
                }));
                this.router.navigate(['/legal-research']);
                break;
                
              case 'risk_assessment':
                localStorage.setItem('current_analysis', JSON.stringify({
                  type: analysisType,
                  result: res,
                  fileName: this.selectedFiles_1.name
                }));
                this.router.navigate(['/risk-assessment']);
                break;
                
              case 'information_extraction':
                localStorage.setItem('current_analysis', JSON.stringify({
                  type: analysisType,
                  result: res,
                  fileName: this.selectedFiles_1.name
                }));
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
// Update the viewContract method
viewContract(contract: ContractDocument) {
  if (contract.analysisResult) {
    try {
      // Store current analysis state
      localStorage.setItem('current_analysis', JSON.stringify({
        type: contract.type,
        result: contract.analysisResult,
        fileName: contract.fileName
      }));

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
  }
}