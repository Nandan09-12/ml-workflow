import { z } from "zod";

export const roleSchema = z.enum(["DRIVE_TESTER", "ADMIN"]);
export const approvalStatusSchema = z.enum([
  "PENDING",
  "APPROVED",
  "REJECTED",
  "SUSPENDED",
]);

export const apiMetaSchema = z.object({
  requestId: z.string().optional(),
  page: z.number().int().positive().optional(),
  pageSize: z.number().int().positive().optional(),
  total: z.number().int().nonnegative().optional(),
});

export const appUserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  fullName: z.string(),
  role: roleSchema,
  approvalStatus: approvalStatusSchema,
});

export const authStatusSchema = z.enum([
  "SIGNED_OUT",
  "PENDING_APPROVAL",
  "APPROVED",
  "SUSPENDED",
]);

export const projectSchema = z.object({
  id: z.string(),
  title: z.string(),
  subtitle: z.string(),
  iconKey: z.enum(["checkin", "inventory", "vendor", "feedback"]),
  accentColor: z.string(),
});

export const apiSuccessEnvelopeSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.literal(true),
    data: dataSchema,
    meta: apiMetaSchema.optional(),
  });

export const apiErrorEnvelopeSchema = z.object({
  success: z.literal(false),
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.unknown().optional(),
  }),
  meta: apiMetaSchema.optional(),
});

export type Role = z.infer<typeof roleSchema>;
export type ApprovalStatus = z.infer<typeof approvalStatusSchema>;
export type AuthStatus = z.infer<typeof authStatusSchema>;
export type AppUser = z.infer<typeof appUserSchema>;
export type Project = z.infer<typeof projectSchema>;
