# Godel - Document Processing Platform

A modern web application for uploading, storing, and processing DOCX documents with AI-powered analysis. Built with React, TypeScript, Supabase, and Tailwind CSS.

## 🚀 Features

- **User Authentication**: Secure sign-up/sign-in with email verification
- **Document Upload**: Drag-and-drop DOCX file upload with progress tracking
- **Document Management**: View, download, and delete uploaded documents
- **Processing Status**: Real-time tracking of document processing status
- **Responsive Design**: Modern UI that works on desktop and mobile devices

## 🏗️ Architecture

### Frontend Stack
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **React Router** for navigation
- **React Query** for data fetching
- **React Dropzone** for file uploads

### Backend & Database
- **Supabase** for authentication, database, and file storage
- **PostgreSQL** database with Row Level Security (RLS)
- **Supabase Storage** for document file storage

## 📁 Project Structure

```
src/
├── components/          # React components
│   ├── Auth.tsx        # Authentication UI
│   ├── Dashboard.tsx   # Main dashboard
│   ├── FileUpload.tsx  # File upload component
│   ├── DocumentList.tsx # Document management
│   └── ui/             # shadcn/ui components
├── hooks/              # Custom React hooks
│   └── useAuth.tsx     # Authentication hook
├── integrations/       # External service integrations
│   └── supabase/       # Supabase client and types
├── pages/              # Page components
│   ├── Index.tsx       # Main page (auth/dashboard)
│   └── NotFound.tsx    # 404 page
└── lib/                # Utility functions
```

## 🔐 Authentication System

### User Registration & Login
- **Sign Up**: Users can create accounts with email, password, and full name
- **Email Verification**: Required email verification for new accounts
- **Sign In**: Secure login with email and password
- **Session Management**: Automatic session persistence and token refresh

### Authentication Flow
1. User visits the application
2. If not authenticated, shows the Auth component with sign-in/sign-up forms
3. After successful authentication, redirects to the Dashboard
4. User session is maintained across browser sessions

## 📤 File Upload System

### Upload Process
1. **File Selection**: Users can drag-and-drop or browse for DOCX files
2. **File Validation**: Only `.docx` files are accepted
3. **Upload Progress**: Real-time progress bar during upload
4. **Storage**: Files are uploaded to Supabase Storage in user-specific folders
5. **Database Record**: Document metadata is saved to the `documents` table

### File Storage Structure
```
Storage Bucket: 'documents'
├── {user_id}/
│   ├── {timestamp}-{random}.docx
│   └── {timestamp}-{random}.docx
```

### Upload Component Features
- Drag-and-drop interface with visual feedback
- File size display
- Upload progress tracking
- Error handling with toast notifications
- Cancel upload functionality

## 🗄️ Database Schema

### Tables

#### `profiles` Table
```sql
CREATE TABLE public.profiles (
  id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  email TEXT,
  full_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  PRIMARY KEY (id)
);
```

#### `documents` Table
```sql
CREATE TABLE public.documents (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users NOT NULL,
  filename TEXT NOT NULL,                    -- Generated unique filename
  original_filename TEXT NOT NULL,           -- Original user filename
  file_path TEXT NOT NULL,                   -- Storage path
  file_size BIGINT,                          -- File size in bytes
  upload_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  processing_status TEXT NOT NULL DEFAULT 'pending' 
    CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
  processed_at TIMESTAMP WITH TIME ZONE,     -- When processing completed
  processing_results JSONB,                  -- AI processing results
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
```

### Row Level Security (RLS)
- **Profiles**: Users can only view/update their own profile
- **Documents**: Users can only access their own documents
- **Storage**: Users can only access files in their own folder

## 🎯 Main Page Buttons & Functionality

### Dashboard Header
- **Sign Out Button**: Logs out the current user and returns to auth page
- **User Info Display**: Shows logged-in user's email

### Statistics Cards
- **Total Documents**: Shows count of all uploaded documents
- **Processing**: Shows count of documents currently being processed
- **Completed**: Shows count of successfully processed documents

### Upload Section
- **Drag & Drop Area**: Accepts DOCX files with visual feedback
- **Upload Button**: Initiates file upload with progress tracking
- **Cancel Button**: Cancels the current upload

### Document List
- **Refresh Button**: Reloads the document list from the database
- **Document Cards**: Each document shows:
  - Original filename
  - File size
  - Upload date
  - Processing date (if completed)
  - Processing status badge
  - Action buttons

### Document Action Buttons
- **Download Button** (📥): Downloads the original file
- **View Results Button** (👁️): Shows processing results (if available)
- **Delete Button** (🗑️): Removes document from storage and database

### Status Badges
- **Pending** (🟡): Document uploaded, waiting for processing
- **Processing** (🔵): Document is currently being processed
- **Completed** (🟢): Processing finished successfully
- **Failed** (🔴): Processing encountered an error

## 🔧 Supabase Integration

### Configuration
```typescript
// src/integrations/supabase/client.ts
const SUPABASE_URL = "https://zpyamkqmvkpsddehyglc.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";

export const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
  auth: {
    storage: localStorage,
    persistSession: true,
    autoRefreshToken: true,
  }
});
```

### Key Features
- **Type Safety**: Full TypeScript support with generated types
- **Real-time Updates**: Automatic session management
- **Storage Integration**: Direct file upload/download
- **Row Level Security**: Secure data access patterns

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Supabase account and project

### Installation
```bash
# Clone the repository
git clone https://github.com/SingularityUS/Godel.git
cd Godel

# Install dependencies
npm install

# Set up environment variables
# Create .env.local with your Supabase credentials
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# Start development server
npm run dev
```

### Database Setup
1. Create a new Supabase project
2. Run the migration file: `supabase/migrations/20250701005835-ff3fec72-36fa-4f23-a6ea-bd3f5368d04e.sql`
3. Create a storage bucket named 'documents'
4. Update the Supabase client configuration

## 🔒 Security Features

- **Row Level Security**: Database-level access control
- **User Isolation**: Users can only access their own data
- **Secure File Storage**: Files stored in user-specific folders
- **Email Verification**: Required for new accounts
- **Session Management**: Secure token handling

## 📱 User Experience

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Loading States**: Visual feedback during operations
- **Error Handling**: User-friendly error messages
- **Toast Notifications**: Success and error feedback
- **Progress Tracking**: Real-time upload progress

## 🔄 Processing Workflow

1. **Upload**: User uploads DOCX file
2. **Storage**: File saved to Supabase Storage
3. **Database**: Document record created with 'pending' status
4. **Processing**: Background process analyzes document (future feature)
5. **Completion**: Status updated to 'completed' with results
6. **Display**: Results available in the document list

## 🛠️ Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Code Style
- TypeScript for type safety
- ESLint for code quality
- Prettier for code formatting
- Component-based architecture

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions, please open an issue on GitHub or contact the development team.
