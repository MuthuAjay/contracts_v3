import { Component, inject } from '@angular/core';
import { AddUserModalComponent } from './add-user-modal/add-user-modal.component';
import {MatDialog, MatDialogModule} from '@angular/material/dialog';
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
  uploadForm!:FormGroup
  selectedFiles: File[] = [];
  selectedFiles_1:any
  loadershow:boolean = false
  extractedValue:any
  showCategory:boolean = false
constructor( private fb:FormBuilder, private apiService: ServicesService, private router:Router){
  this.uploadForm = this.fb.group({
    analysisType: [''],
  })
}

  togglePopup() {
    this.isPopupVisible = !this.isPopupVisible;
  }
  readonly dialog = inject(MatDialog);
  users = [
    { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Admin' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'User' }
  ];

  displayedColumns: string[] = ['id', 'name', 'email', 'role', 'actions'];
  openDialog() {
    const dialogRef = this.dialog.open(AddUserModalComponent,{
      height: '400px',
      width: '600px',
    });
    
    dialogRef.afterClosed().subscribe(result => {
      
      console.log(`Dialog result: ${result}`);
    });
  }
  onSubmit(){
      if (this.extractedValue) {

        if(this.uploadForm.value.analysisType == "custom_analysis"){
          this.router.navigate(['/Analytics']);
        }else{

          this.extractedValue.type = this.uploadForm.value.analysisType;
          this.extractedValue.custom_query = ''
         
          this.apiService.analyze(this.extractedValue).subscribe((res:any) => {
            console.log(res)
            console.log('Upload complete', res);
            if(res){
              this.loadershow = true
              localStorage.setItem("extraction", JSON.stringify(res));
              this.router.navigate(['/extraction']);
            }
            
          })
        }
       
      }
      // localStorage.setItem('extracted', JSON.stringify(res));
    // })

  }
  fileUpload(e:any){
    console.log(e)
  }
  uploadFiles() {
    if (this.selectedFiles.length === 0) {
      alert("No files selected!");
      return;
    }

    const formData = new FormData();
    this.selectedFiles.forEach(file => formData.append('file', file));

    // Simulate upload request (replace with actual HTTP service)
    console.log('Uploading...', formData);
    alert('Files uploaded successfully!');
  }

  onFileSelected(event: any) {
    // alert("Hi")
    const files: File[] = event.target.files[0];
    this.selectedFiles_1 = event.target.files[0];
    console.log('Selected files:', files);


    const formData = new FormData();
    formData.append('file', this.selectedFiles_1);
    this.apiService.upload_file(formData).subscribe((res:any) => {
      if (res) {
          localStorage.setItem("extractionInfo", JSON.stringify(res));
          this.extractedValue = res
          this.showCategory = true
          this.loadershow = true
      }
})



  }

}