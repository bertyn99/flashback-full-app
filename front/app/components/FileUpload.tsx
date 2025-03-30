// src/components/FileUpload.tsx
import { useState } from 'react'
import { Upload, File, Loader2 } from 'lucide-react'
import { Button } from '~/components/ui/button'
import { Progress } from '~/components/ui/progress'
import { Card, CardContent } from '~/components/ui/card'
import { toast } from 'sonner'
import { cn } from '~/lib/utils'

interface FileUploadProps {
  onUploadComplete: (taskId: string) => void
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) setFile(droppedFile)
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      
      if (data.taskId) {
        onUploadComplete(data.taskId)
        toast.success('File uploaded successfully')
      }
    } catch (error) {
      toast.error('Failed to upload file')
      console.error(error)
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center",
            file ? "border-green-500" : "border-gray-300"
          )}
        >
          {file ? (
            <div className="space-y-4">
              <File className="w-12 h-12 mx-auto text-gray-400" />
              <div>
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <Upload className="w-12 h-12 mx-auto text-gray-400" />
              <div>
                <p className="text-sm font-medium">
                  Drop your file here or click to browse
                </p>
                <p className="text-xs text-gray-500">
                  Supports PDF and DOC files
                </p>
              </div>
            </div>
          )}
          <input
            type="file"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            accept=".pdf,.doc,.docx"
          />
        </div>

        {file && (
          <div className="mt-6 space-y-4">
            <Progress value={progress} />
            <Button
              className="w-full"
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {uploading ? 'Uploading...' : 'Upload and Process'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}