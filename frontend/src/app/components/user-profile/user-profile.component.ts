import { Component } from '@angular/core';

@Component({
    selector: 'app-user-profile',
    templateUrl: './user-profile.component.html',
    styleUrls: ['./user-profile.component.scss'],
    standalone: false
})
export class UserProfileComponent {
  user = {
    name: 'John Doe',
    email: 'john@example.com',
    role: 'Admin'
  };
}