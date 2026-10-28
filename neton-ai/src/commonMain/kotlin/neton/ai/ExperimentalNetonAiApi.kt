package neton.ai

/** Stability is governed by the independent Neton AI release line. */
@RequiresOptIn(level = RequiresOptIn.Level.ERROR, message = "Neton AI is experimental; explicitly opt in and pin the AI and framework versions.")
@Retention(AnnotationRetention.BINARY)
@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.PROPERTY, AnnotationTarget.TYPEALIAS)
public annotation class ExperimentalNetonAiApi
