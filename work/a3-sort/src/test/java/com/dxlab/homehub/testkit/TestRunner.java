package com.dxlab.homehub.testkit;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

/**
 * Minimal in-house test runner (the hub build predates JUnit adoption).
 * Runs every public no-arg method whose name starts with "test" on each given class.
 */
public final class TestRunner {
    private TestRunner() {
    }

    public static void main(String[] args) throws Exception {
        String[] classes = args.length > 0 ? args : AllTests.CLASSES;
        int passed = 0;
        List<String> failures = new ArrayList<String>();
        for (int c = 0; c < classes.length; c++) {
            Class<?> k = Class.forName(classes[c]);
            Method[] ms = k.getMethods();
            Arrays.sort(ms, new Comparator<Method>() {
                public int compare(Method a, Method b) {
                    return a.getName().compareTo(b.getName());
                }
            });
            for (int i = 0; i < ms.length; i++) {
                Method m = ms[i];
                if (!m.getName().startsWith("test") || m.getParameterTypes().length != 0
                        || Modifier.isStatic(m.getModifiers())) {
                    continue;
                }
                Object inst = k.getDeclaredConstructor().newInstance();
                try {
                    m.invoke(inst);
                    passed++;
                } catch (InvocationTargetException ex) {
                    Throwable t = ex.getCause();
                    failures.add(k.getSimpleName() + "." + m.getName() + ": " + t);
                }
            }
        }
        for (int i = 0; i < failures.size(); i++) {
            System.out.println("FAIL " + failures.get(i));
        }
        System.out.println("tests: " + (passed + failures.size()) + ", passed: " + passed
                + ", failed: " + failures.size());
        if (!failures.isEmpty()) {
            System.exit(1);
        }
    }
}
