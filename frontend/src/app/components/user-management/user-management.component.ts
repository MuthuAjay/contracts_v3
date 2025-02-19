import { Component, inject } from '@angular/core';
import { AddUserModalComponent } from './add-user-modal/add-user-modal.component';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ServicesService } from '../../services.service';
import { Router } from '@angular/router';

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

  onSubmit() {
    if (this.extractedValue) {
      const analysisType = this.uploadForm.value.analysisType;
      console.log('Selected analysis type:', analysisType); // Debug log

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
            console.log('API Response:', res); // Debug log
            
            // Handle different analysis types
            switch (analysisType) {
              case 'contract_review':
                console.log('Handling contract review'); // Debug log
                localStorage.setItem('contract_review', JSON.stringify(res));
                this.router.navigate(['/contract-review']).then(() => {
                  console.log('Navigation complete'); // Debug log
                }).catch(err => {
                  console.error('Navigation failed:', err);
                });
                break;

              case 'contract_summary':
                console.log('Handling contract summary'); // Debug log
                localStorage.setItem('contract_review', JSON.stringify(res));
                this.router.navigate(['/contract-review']).then(() => {
                  console.log('Navigation complete'); // Debug log
                }).catch(err => {
                  console.error('Navigation failed:', err);
                });
                break;
              
              case 'legal_research':
                localStorage.setItem('legal_research', JSON.stringify(res));
                this.router.navigate(['/legal-research']);
                break;
                
              case 'risk_assessment':
                localStorage.setItem('risk_assessment', JSON.stringify(res));
                this.router.navigate(['/risk-assessment']);
                break;
                
              case 'information_extraction':
                localStorage.setItem('extraction', JSON.stringify(res));
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
    
    this.apiService.upload_file(formData).subscribe({
      next: (res: any) => {
        if (res) {
          localStorage.setItem("extractionInfo", JSON.stringify(res));
          this.extractedValue = res;
          this.showCategory = true;
          this.loadershow = true;
        }
      },
      error: (error) => {
        console.error('File upload failed:', error);
        this.loadershow = false;
        // Handle error - you might want to show an error message to the user
      }
    });
  }
}