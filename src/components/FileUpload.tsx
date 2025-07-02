import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/use-toast';
import { Upload, FileText, X, CheckCircle } from 'lucide-react';
import { Json } from '@supabase/supabase-js';

interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number | null;
  upload_date: string;
  processing_status: string;
  processed_at: string | null;
  processing_results: Json | null;
  user_id: string;
}

interface FileUploadProps {
  onDocumentUploaded: (document: Document) => void;
}

export function FileUpload({ onDocumentUploaded }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const { user } = useAuth();
  const { toast } = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setSelectedFile(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 1,
    multiple: false
  });

  const uploadFile = async () => {
    if (!selectedFile || !user) {
      toast({
        title: "Error",
        description: "Please select a file and ensure you're logged in.",
        variant: "destructive",
      });
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // Generate unique filename
      const fileExt = selectedFile.name.split('.').pop();
      const fileName = `${Date.now()}-${Math.random().toString(36).substring(2)}.${fileExt}`;
      const filePath = `${user.id}/${fileName}`;

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Upload to Supabase Storage
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('documents')
        .upload(filePath, selectedFile);

      if (uploadError) throw uploadError;

      setUploadProgress(100);

      // Save document metadata to database
      const { data: docData, error: docError } = await supabase
        .from('documents')
        .insert({
          user_id: user.id,
          filename: fileName,
          original_filename: selectedFile.name,
          file_path: filePath,
          file_size: selectedFile.size,
          processing_status: 'pending'
        })
        .select()
        .single();

      if (docError) throw docError;

      // Notify parent component *before* starting backend processing
      onDocumentUploaded(docData);
      
      // Trigger backend processing
      console.log('Triggering backend processing for:', docData.file_path);
      fetch('http://localhost:5001/process-document', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ file_path: docData.file_path }),
      })
      .then(async response => {
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Backend processing failed');
        }
        return response.json();
      })
      .then(processingResults => {
        console.log('Backend processing successful:', processingResults);
        // Here you would typically update the document's status and results
        // in your Supabase 'documents' table.
        // For now, we'll just show a success toast.
        toast({
          title: "Processing Complete",
          description: "The document has been successfully processed by the backend.",
        });
      })
      .catch(error => {
        console.error('Backend processing error:', error);
        toast({
          title: "Processing Error",
          description: `Failed to process document: ${error.message}`,
          variant: "destructive",
        });
      });

      // Clear the form
      setSelectedFile(null);
      setUploadProgress(0);

      toast({
        title: "Upload successful",
        description: "Your document has been uploaded and is queued for processing.",
      });

    } catch (error) {
      console.error('Upload error:', error);
      toast({
        title: "Upload failed",
        description: "There was an error uploading your document. Please try again.",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setUploadProgress(0);
  };

  return (
    <div className="space-y-4">
      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center space-y-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <Upload className="h-8 w-8 text-blue-600" />
            </div>
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop your DOCX file here' : 'Upload a DOCX document'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Drag and drop or click to browse your files
              </p>
            </div>
            <p className="text-xs text-gray-400">
              Only .docx files are supported
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Selected File Display */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            {!uploading && (
              <Button
                variant="ghost"
                size="sm"
                onClick={removeFile}
                className="text-red-500 hover:text-red-700"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="h-2" />
            </div>
          )}

          {/* Upload Button */}
          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={removeFile}
              disabled={uploading}
            >
              Cancel
            </Button>
            <Button
              onClick={uploadFile}
              disabled={uploading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {uploading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Uploading...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Upload className="h-4 w-4" />
                  <span>Upload Document</span>
                </div>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
