/**
 * Shared Framer Motion variants for entrance + stagger choreography.
 * Pair with the `.hover-lift` / `.press` CSS utilities for hover states.
 */
import type { Variants, Transition } from "motion/react";

const EASE = [0.22, 1, 0.36, 1] as const;

/** Page root — fades in and staggers its direct children upward. */
export const pageStagger: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.04 },
  },
};

/** A staggered child — fades + slides up into place. */
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: EASE } },
};

/** Tighter container for dense lists (chips, table rows). */
export const listStagger: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.045, delayChildren: 0.03 } },
};

/** A dense-list child — quick fade + small rise. */
export const fadeUpSm: Variants = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.32, ease: EASE } },
};

/** Standard entrance props — spread onto a motion element. */
export const entrance = {
  initial: "hidden" as const,
  animate: "show" as const,
};

/** Spring used for hover/tap interactions. */
export const springy: Transition = { type: "spring", stiffness: 400, damping: 28 };
