import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ServicesService {
  private apiUrl =  'http://localhost:8003/api/';
  constructor(private http:HttpClient) { }


  upload_file(data:any) {
    return this.http.post(this.apiUrl + 'upload', data);
  }

  analyze(data:any) {
    return this.http.post(this.apiUrl + 'analyze', data);
  }

}
