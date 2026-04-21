import type { FileState, Region } from "@/lib/types/domain";

export function formatRegion(region: Region): string {
  switch (region) {
    case "NE_UP":
      return "NE-UP";
    case "CENTRAL":
      return "Central";
    case "SOUTH_FLORIDA":
      return "South/Florida";
  }
}

export function formatFileState(fileState: FileState): string {
  switch (fileState) {
    case "FILE_PENDING":
      return "File Pending";
    case "ATTACHED":
      return "Attached";
    case "NOT_REQUIRED":
      return "Not Required";
  }
}
