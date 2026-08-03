import { LoginForm } from "@/components/LoginForm";
import { ProductStoryPanel } from "@/components/ProductStoryPanel";

export const metadata = {
  title: "Нэвтрэх — Улаанбаатар Үл Хөдлөх Хөрөнгө",
};

// Only a same-site relative path is ever honored as a post-login
// destination -- an absolute or protocol-relative ("//evil.com") value in
// ?next= would otherwise turn this into an open redirect.
function sanitizeNext(next: string | string[] | undefined): string {
  const value = Array.isArray(next) ? next[0] : next;
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/";
  return value;
}

export default function LoginPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined };
}) {
  const next = sanitizeNext(searchParams.next);

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <div className="md:w-[45%] lg:w-[55%]">
        <ProductStoryPanel />
      </div>
      <div className="flex flex-1 items-center justify-center bg-surface-page px-6 py-12 sm:px-10 md:w-[55%] lg:w-[45%]">
        <LoginForm next={next} />
      </div>
    </div>
  );
}
