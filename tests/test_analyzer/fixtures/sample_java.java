/** Sample Java code used as test fixture for Java analyzer tests. */

public class Sample {

    public String greet(String name) {
        return "Hello, " + name;
    }

    public int add(int a, int b) {
        return a + b;
    }

    // Insecure code: SQL concatenation
    public void insecureSql(String userId) {
        String query = "SELECT * FROM users WHERE id = " + userId;
        java.sql.Statement stmt = connection.createStatement();
        stmt.executeQuery(query);
    }

    // Insecure code: command injection
    public void insecureCommand(String cmd) throws Exception {
        Runtime.getRuntime().exec(cmd);
    }
}
