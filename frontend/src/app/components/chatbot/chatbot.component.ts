import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked, OnDestroy } from '@angular/core';
import { ServicesService } from '../../services.service';
import { Subject, takeUntil } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface ChatMessage {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
  status: 'sending' | 'sent' | 'error';
}

interface ExtractionData {
  type: string;
  custom_query: string;
  [key: string]: any;
}

@Component({
  selector: 'app-chatbot',
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class ChatbotComponent implements OnInit, AfterViewChecked, OnDestroy {
  @ViewChild('messageContainer') private messageContainer!: ElementRef;
  @ViewChild('inputArea') private inputArea!: ElementRef;

  public messages: ChatMessage[] = [];
  public newMessage = '';
  public isLoading = false;
  public error: string | null = null;
  public loadershow = true;
  
  private destroy$ = new Subject<void>();
  private readonly MAX_RETRIES = 3;
  private retryCount = 0;

  constructor(private apiService: ServicesService) {}

  ngOnInit(): void {
    this.initializeChat();
    this.loadStoredMessages();
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.saveMessages();
  }

  private initializeChat(): void {
    const welcomeMessage: ChatMessage = {
      id: this.generateMessageId(),
      content: 'Hello! How can I help you today?',
      isBot: true,
      timestamp: new Date(),
      status: 'sent'
    };
    
    this.messages = [welcomeMessage];
  }

  private loadStoredMessages(): void {
    try {
      const storedMessages = localStorage.getItem('chatMessages');
      if (storedMessages) {
        const parsedMessages = JSON.parse(storedMessages);
        this.messages = parsedMessages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
      }
    } catch (error) {
      console.error('Error loading stored messages:', error);
    }
  }

  private saveMessages(): void {
    try {
      localStorage.setItem('chatMessages', JSON.stringify(this.messages));
    } catch (error) {
      console.error('Error saving messages:', error);
    }
  }

  public async sendMessage(): Promise<void> {
    if (!this.newMessage.trim() || this.isLoading) return;

    const userMessage: ChatMessage = {
      id: this.generateMessageId(),
      content: this.newMessage.trim(),
      isBot: false,
      timestamp: new Date(),
      status: 'sending'
    };

    this.messages.push(userMessage);
    this.isLoading = true;
    this.error = null;
    const messageContent = this.newMessage;
    this.newMessage = '';
    this.scrollToBottom();

    try {
      const extractedData = this.getExtractionData();
      const response = await this.sendMessageToApi(messageContent, extractedData);
      this.handleApiResponse(response);
      userMessage.status = 'sent';
    } catch (error) {
      this.handleError(error);
      userMessage.status = 'error';
    } finally {
      this.isLoading = false;
      this.saveMessages();
    }
  }

  private async sendMessageToApi(message: string, extractedData: ExtractionData) {
    return new Promise((resolve, reject) => {
      this.apiService.analyze({
        ...extractedData,
        type: 'custom_analysis',
        custom_query: message
      })
      .pipe(
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (response) => resolve(response),
        error: (error) => {
          if (this.retryCount < this.MAX_RETRIES) {
            this.retryCount++;
            setTimeout(() => {
              this.sendMessageToApi(message, extractedData)
                .then(resolve)
                .catch(reject);
            }, 1000 * this.retryCount);
          } else {
            this.retryCount = 0;
            reject(error);
          }
        }
      });
    });
  }

  private handleApiResponse(response: any): void {
    const botMessage: ChatMessage = {
      id: this.generateMessageId(),
      content: response['Custom Analysis'] || 'I apologize, but I couldn\'t process that properly.',
      isBot: true,
      timestamp: new Date(),
      status: 'sent'
    };
    
    this.messages.push(botMessage);
    this.scrollToBottom();
  }

  private handleError(error: any): void {
    console.error('Error in chat:', error);
    this.error = 'Sorry, there was an error processing your message. Please try again.';
    
    const errorMessage: ChatMessage = {
      id: this.generateMessageId(),
      content: this.error,
      isBot: true,
      timestamp: new Date(),
      status: 'error'
    };
    
    this.messages.push(errorMessage);
  }

  public onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.loadershow = false;
      this.sendMessage();
    }
  }

  private getExtractionData(): ExtractionData {
    try {
      const extractedData = localStorage.getItem('extractionInfo');
      if (!extractedData) {
        return {
          type: 'custom_analysis',
          custom_query: ''
        };
      }
      return JSON.parse(extractedData);
    } catch (error) {
      console.error('Error parsing extraction data:', error);
      return {
        type: 'custom_analysis',
        custom_query: ''
      };
    }
  }

  private scrollToBottom(): void {
    try {
      this.messageContainer.nativeElement.scrollTop = 
        this.messageContainer.nativeElement.scrollHeight;
    } catch (err) {}
  }

  private generateMessageId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  public onInput(): void {
    const textarea = this.inputArea.nativeElement;
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  }

  public clearChat(): void {
    this.messages = [];
    this.initializeChat();
    localStorage.removeItem('chatMessages');
  }
}