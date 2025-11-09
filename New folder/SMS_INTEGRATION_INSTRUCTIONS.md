# SMS Feature Integration Instructions

## ✅ What's Already Done:

1. **Backend** - SMS routes and Twilio service are set up
   - Routes: `/api/sms/managers`, `/api/sms/draft`, `/api/sms/send`, `/api/sms/test`
   - Service: `server/services/twilio/sms_service.py`
   - Managers configured: John, Jason, T Wright, Tiffany Larkins

2. **Frontend** - SMS component created
   - Component: `client/app/components/SMSPage.tsx`
   - Route: `client/app/sms/page.tsx`
   - Access at: http://localhost:3000/sms

## 📋 To Add SMS to Main Navigation:

### Step 1: Update `client/app/page.tsx`

**Find this line (around line 10):**
```typescript
import {
  Inbox, CheckSquare, Users, Brain, Sparkles, Calendar, UsersRound
} from 'lucide-react';
```

**Change to:**
```typescript
import {
  Inbox, CheckSquare, Users, Brain, Sparkles, Calendar, UsersRound, MessageSquare
} from 'lucide-react';
```

**Find this line (around line 7):**
```typescript
import OperationsChat from './components/OperationsChat';
```

**Add after it:**
```typescript
import SMSPage from './components/SMSPage';
```

**Find this line (around line 16):**
```typescript
const [currentPage, setCurrentPage] = useState<'triage' | 'todo' | 'delegations' | 'calendar' | 'team-board'>('triage');
```

**Change to:**
```typescript
const [currentPage, setCurrentPage] = useState<'triage' | 'todo' | 'delegations' | 'calendar' | 'team-board' | 'sms'>('triage');
```

**Find the navigation buttons section (around line 170) and add this button AFTER the Team Board button:**
```typescript
<button
  onClick={() => setCurrentPage('sms')}
  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center space-x-2 ${
    currentPage === 'sms'
      ? 'bg-red-500 text-white'
      : 'text-gray-300 hover:bg-gray-700'
  }`}
>
  <MessageSquare className="h-4 w-4" />
  <span>📱 Text Managers</span>
</button>
```

**Find the page content section (around line 230) where it shows different pages:**
```typescript
{currentPage === 'triage' ? (
  <TriagePage onAddToTodo={handleAddToTodo} onNavigate={setCurrentPage} />
) : currentPage === 'todo' ? (
  <TodoPage onNavigate={setCurrentPage} />
) : currentPage === 'calendar' ? (
  <CalendarPage />
) : currentPage === 'team-board' ? (
  <TeamBoardPage onNavigate={setCurrentPage} />
) : (
  <DelegationsPage />
)}
```

**Change to:**
```typescript
{currentPage === 'triage' ? (
  <TriagePage onAddToTodo={handleAddToTodo} onNavigate={setCurrentPage} />
) : currentPage === 'todo' ? (
  <TodoPage onNavigate={setCurrentPage} />
) : currentPage === 'calendar' ? (
  <CalendarPage />
) : currentPage === 'team-board' ? (
  <TeamBoardPage onNavigate={setCurrentPage} />
) : currentPage === 'sms' ? (
  <SMSPage />
) : (
  <DelegationsPage />
)}
```

## 🧪 Testing:

1. **Test the backend first:**
   ```bash
   cd server
   python run_server.py
   ```
   Then visit: http://localhost:8002/api/sms/managers
   You should see your 4 managers listed.

2. **Test sending:**
   Visit: http://localhost:8002/api/sms/test
   This will send a test message to your phone.

3. **Start the frontend:**
   ```bash
   cd client
   npm run dev
   ```
   Then visit: http://localhost:3000
   Click the "📱 Text Managers" button

## 💡 Usage:

1. **Draft a message with AI:**
   - Type something like "Need coverage Friday dinner 5-9pm"
   - Click "Draft Message with AI"
   - The AI will create a professional message

2. **Edit the message** if needed

3. **Select which managers** to send to (or leave all selected)

4. **Hit Send!**

## 📱 Your Configured Managers:
- **John (MP)**: +1 832-756-5450
- **Jason**: +1 248-915-8176
- **T Wright**: +1 586-722-4594  
- **Tiffany Larkins**: +1 313-912-5662

Enjoy your new texting feature! 🎉
