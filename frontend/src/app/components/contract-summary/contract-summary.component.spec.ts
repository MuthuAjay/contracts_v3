import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ContractSummaryComponent } from './contract-summary.component';

describe('ContractSummaryComponent', () => {
  let component: ContractSummaryComponent;
  let fixture: ComponentFixture<ContractSummaryComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ContractSummaryComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ContractSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
