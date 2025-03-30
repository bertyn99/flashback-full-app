// src/pages/Dashboard.tsx
import { FileUpload } from '~/components/FileUpload'
import { VideoProcessing } from '~/components/VideoProcessing'
import { VideoList } from '~/components/VideoList'
import { useState } from 'react'

export function Dashboard() {
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
      </div>
      
      <div className="grid gap-8">
        <FileUpload onUploadComplete={setCurrentTaskId} />
        {currentTaskId && (
          <VideoProcessing taskId={currentTaskId} />
        )}
        <VideoList />
      </div>
    </div>
  )
}