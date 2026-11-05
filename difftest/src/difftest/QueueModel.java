package difftest;

import java.util.List;

/**
 * What the difftest needs from a Dafny queue model, in plain Java types.
 *
 * Dafny compiles a model to Java classes whose names and types depend on how the model was
 * written (BigInteger or int, tuples, datatypes ...). An adapter class implements this
 * interface by calling the compiled model, so ANY Dafny translation of RingEventQueue can be
 * compared with the Java class without changing DiffTest.
 *
 * The adapter for the model in formal/ is RingQueueAdapter. For your own (AI-written) model,
 * ask the AI to write one too (docs/PROMPTS.md, P-1b) and run `make difftest-mine`.
 */
public interface QueueModel {
    /** Called once, right after the no-argument constructor. */
    void init(int capacity);

    /** "OK" or "FULL". The event is identified by id; critical is the LEAK/OVERHEAT flag. */
    String offer(int id, boolean critical);

    /** id of the removed event, or null when the queue is empty. */
    Integer poll();

    /** id of the oldest event, or null when the queue is empty. */
    Integer peek();

    int size();

    boolean isEmpty();

    int capacity();

    void clear();

    /** ids, oldest first. */
    List<Integer> snapshot();
}
