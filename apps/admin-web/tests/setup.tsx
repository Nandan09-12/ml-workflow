import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

declare global {
  var __mockPathname: string;
}

globalThis.__mockPathname = "/dashboard";

vi.mock("next/navigation", () => ({
  usePathname: () => globalThis.__mockPathname,
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
});