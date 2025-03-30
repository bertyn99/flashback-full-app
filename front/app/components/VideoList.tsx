// src/components/VideoList.tsx
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Download, Play } from 'lucide-react'

interface Video {
  id: string
  title: string
  thumbnail: string
  duration: string
  status: 'completed' | 'processing' | 'failed'
}

export function VideoList() {
  const videos: Video[] = [] // Replace with actual data fetching

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generated Videos</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4">
          {videos.map((video) => (
            <div
              key={video.id}
              className="flex items-center justify-between p-4 border rounded-lg"
            >
              <div className="flex items-center space-x-4">
                <div className="w-32 h-20 bg-gray-200 rounded">
                  {/* Thumbnail */}
                </div>
                <div>
                  <h3 className="font-medium">{video.title}</h3>
                  <p className="text-sm text-gray-500">{video.duration}</p>
                </div>
              </div>
              <div className="flex space-x-2">
                <Button size="sm" variant="outline">
                  <Play className="h-4 w-4 mr-2" />
                  Preview
                </Button>
                <Button size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}