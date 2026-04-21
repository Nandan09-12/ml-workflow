import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

declare global {
  var __mockPathname: string;
  var __mockSearchParams: string;
  var __mockSearchParamsInstance: URLSearchParams;
  var __mockRouterReplace: ReturnType<typeof vi.fn>;
  var __mockRouterPush: ReturnType<typeof vi.fn>;
}

globalThis.__mockPathname = "/dashboard";
globalThis.__mockSearchParams = "";
globalThis.__mockSearchParamsInstance = new URLSearchParams();
globalThis.__mockRouterReplace = vi.fn();
globalThis.__mockRouterPush = vi.fn();

function getMockSearchParams() {
  const nextSearchParams = globalThis.__mockSearchParams;

  if (globalThis.__mockSearchParamsInstance.toString() !== nextSearchParams) {
    globalThis.__mockSearchParamsInstance = new URLSearchParams(nextSearchParams);
  }

  return globalThis.__mockSearchParamsInstance;
}

vi.mock("next/navigation", () => ({
  usePathname: () => globalThis.__mockPathname,
  useSearchParams: () => getMockSearchParams(),
  useRouter: () => ({
    push: globalThis.__mockRouterPush,
    replace: globalThis.__mockRouterReplace,
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  redirect: vi.fn(),
}));

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("next/image", () => ({
  default: ({ src, alt, priority: _priority, ...props }: React.ImgHTMLAttributes<HTMLImageElement> & { src: string; alt: string; priority?: boolean }) => <img src={src} alt={alt} {...props} />,
}));

afterEach(() => {
  cleanup();
  globalThis.__mockPathname = "/dashboard";
  globalThis.__mockSearchParams = "";
  globalThis.__mockSearchParamsInstance = new URLSearchParams();
  globalThis.__mockRouterReplace.mockReset();
  globalThis.__mockRouterPush.mockReset();
});