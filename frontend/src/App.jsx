"use client"

import { useState } from "react"
import axios from "axios"
import { Briefcase, Search, Send, Loader2 } from "lucide-react"

export default function LinkedInAutoApply() {
  const [keywords, setKeywords] = useState("")
  const [status, setStatus] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleApply = async () => {
    if (!keywords.trim()) {
      setStatus("Please enter job keywords")
      return
    }

    setIsLoading(true)
    setStatus("Sending request to backend...")

    try {
      const res = await axios.post("http://localhost:8000/apply/linkedin", {
        keywords,
        job_type: "any", // this is ignored by backend now
      })
      setStatus(res.data.message)
    } catch (err) {
      console.error(err)
      setStatus("Failed to trigger job application. Make sure backend is running.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="bg-white shadow-xl rounded-3xl p-8 max-w-md w-full border border-gray-100 transition-all duration-300 hover:shadow-2xl">
        <div className="flex items-center justify-center mb-6">
          <div className="bg-blue-600 p-3 rounded-2xl">
            <Briefcase className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold ml-3 text-blue-700">LinkedIn Auto Apply</h1>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Job Keywords</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-xl pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="e.g. software engineer, full stack, frontend"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
              />
            </div>
          </div>

          <button
            onClick={handleApply}
            disabled={isLoading}
            className="w-full bg-blue-600 text-white font-semibold py-3 px-4 rounded-xl hover:bg-blue-700 transition-all duration-300 flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Send className="h-5 w-5" />
                <span>Start Applying</span>
              </>
            )}
          </button>

          {status && (
            <div
              className={`mt-4 p-4 rounded-xl text-sm font-medium ${
                status.includes("Failed") || status.includes("Please enter")
                  ? "bg-red-50 text-red-700 border border-red-200"
                  : status.includes("Sending")
                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                  : "bg-green-50 text-green-700 border border-green-200"
              }`}
            >
              {status}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
