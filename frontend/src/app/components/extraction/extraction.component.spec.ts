import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExtractionComponent } from './extraction.component';

describe('ExtractionComponent', () => {
  let component: ExtractionComponent;
  let fixture: ComponentFixture<ExtractionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExtractionComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ExtractionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
